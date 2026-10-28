# Saved experiments, in a SQLite database (app.config["EXPERIMENTS_DB"]). Every run is stored without a name so it
# can be saved afterwards; saving names it. Unnamed runs older than UNSAVED_RUN_DAYS are deleted.
import json
import os
import sqlite3
from dataclasses import asdict, fields
from datetime import datetime, timedelta, timezone

from flask import current_app, g

from sanitizer.pipeline import Result

UNSAVED_RUN_DAYS = 1

SCHEMA = """
CREATE TABLE IF NOT EXISTS experiments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,              -- NULL until the experiment is saved
    prompt TEXT NOT NULL,
    data TEXT NOT NULL,
    settings TEXT NOT NULL, -- JSON: which mitigation toggles were on
    result TEXT,            -- JSON of the pipeline Result; NULL for a draft saved without running
    created_at TEXT NOT NULL,
    saved_at TEXT
)
"""


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# One connection per request, closed by close_db
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["EXPERIMENTS_DB"], timeout=10)
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_app(app):
    path = app.config["EXPERIMENTS_DB"]
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with sqlite3.connect(path) as db:
        db.execute(SCHEMA)
    db.close()
    app.teardown_appcontext(close_db)


def _result_to_json(result):
    return json.dumps(asdict(result)) if result is not None else None


# Fields missing from an older saved result default to empty ([], "", False), so old experiments still load if
# Result gains a field
def _result_from_json(text):
    if not text:
        return None
    saved = json.loads(text)
    return Result(**{f.name: saved[f.name] if f.name in saved else f.type() for f in fields(Result)})


# Browsers send textarea newlines as \r\n, so compare inputs without them
def _same_inputs(row, prompt, data, settings):
    def norm(s):
        return s.replace("\r\n", "\n")
    return (norm(row["prompt"]) == norm(prompt) and norm(row["data"]) == norm(data)
            and json.loads(row["settings"]) == settings)


def _as_experiment(row):
    if row is None:
        return None
    experiment = dict(row)
    experiment["settings"] = json.loads(row["settings"])
    experiment["result"] = _result_from_json(row["result"])
    return experiment


# SQLite INTEGER is signed 64-bit; ids outside it can't exist and would raise OverflowError when bound
MAX_ID = 2**63 - 1


def _valid_id(experiment_id):
    return experiment_id is not None and 0 < experiment_id <= MAX_ID


def _row(experiment_id):
    if not _valid_id(experiment_id):
        return None
    return get_db().execute("SELECT * FROM experiments WHERE id = ?", (experiment_id,)).fetchone()


# Store a finished run (unnamed) and return its id
def record_run(prompt, data, settings, result):
    db = get_db()
    cutoff = (datetime.now(timezone.utc) - timedelta(days=UNSAVED_RUN_DAYS)).isoformat(timespec="seconds")
    db.execute("DELETE FROM experiments WHERE name IS NULL AND created_at < ?", (cutoff,))
    cursor = db.execute(
        "INSERT INTO experiments (prompt, data, settings, result, created_at) VALUES (?, ?, ?, ?, ?)",
        (prompt, data, json.dumps(settings), _result_to_json(result), _now()),
    )
    db.commit()
    return cursor.lastrowid


# Save the experiment on the page and return (its id, whether run_id had expired). The results of run_id (the run
# shown on the page) or of experiment_id (the saved experiment being edited) are kept if they were produced from
# these same inputs; otherwise the experiment is saved as a draft without results. experiment_id is updated in place
# if it exists.
def save_experiment(name, prompt, data, settings, run_id=None, experiment_id=None):
    db = get_db()
    run, existing = _row(run_id), _row(experiment_id)
    run_expired = run_id is not None and run is None
    if existing is not None and existing["name"] is None:
        existing = None

    result = None
    for row in (run, existing):
        if row is not None and row["result"] and _same_inputs(row, prompt, data, settings):
            result = row["result"]
            break

    now = _now()
    if existing is not None:
        db.execute(
            "UPDATE experiments SET name = ?, prompt = ?, data = ?, settings = ?, result = ?, saved_at = ? WHERE id = ?",
            (name, prompt, data, json.dumps(settings), result, now, existing["id"]),
        )
        saved_id = existing["id"]
    elif result is not None and run["name"] is None:  # the run shown on the page: name it instead of copying it
        db.execute("UPDATE experiments SET name = ?, saved_at = ? WHERE id = ?", (name, now, run["id"]))
        saved_id = run["id"]
    else:
        cursor = db.execute(
            "INSERT INTO experiments (name, prompt, data, settings, result, created_at, saved_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (name, prompt, data, json.dumps(settings), result, now, now),
        )
        saved_id = cursor.lastrowid
    db.commit()
    return saved_id, run_expired


# A saved experiment, with settings as a dict and result as a Result (or None for a draft); None if not found
def get_experiment(experiment_id):
    row = _row(experiment_id)
    return _as_experiment(row) if row is not None and row["name"] is not None else None


def list_experiments():
    rows = get_db().execute("SELECT * FROM experiments WHERE name IS NOT NULL ORDER BY saved_at DESC, id DESC").fetchall()
    return [_as_experiment(row) for row in rows]


def count_experiments():
    return get_db().execute("SELECT COUNT(*) FROM experiments WHERE name IS NOT NULL").fetchone()[0]


def delete_experiment(experiment_id):
    if not _valid_id(experiment_id):
        return
    db = get_db()
    db.execute("DELETE FROM experiments WHERE id = ? AND name IS NOT NULL", (experiment_id,))
    db.commit()
