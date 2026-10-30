from flask import Blueprint, abort, redirect, render_template, request, url_for
#from ollama import chat
from sanitizer.config import LLM_MODEL
from sanitizer.llm import LLMUnavailable

from . import experiments
from .mitigations import run_experiment
from .uploads import UploadError, read_uploads


main = Blueprint("main", __name__)

# The mitigation toggles and baseline checkbox on the form, and whether each starts on. Saved with each experiment.
DEFAULT_SETTINGS = {
    "mit_hardening": True,
    "mit_deobfuscation": True,
    "mit_regex": True,
    "mit_bow": True,
    "mit_validation": True,
    "mit_sanitization": False,
    "compare_baseline": True,
}

# Longest experiment name accepted, in characters
NAME_LENGTH = 120

# The model the pipeline uses (set in sanitizer/config.py), shown in the page footer
model = LLM_MODEL

# Unchecked checkboxes aren't submitted, so a posted form's settings are just which toggles are present
def form_settings(form):
    return {name: name in form for name in DEFAULT_SETTINGS}


# The source data: the text of any uploaded files, which replace the text box, otherwise the text box. Raises
# UploadError for a file that can't be read.
def form_data(req):
    return read_uploads(req.files.getlist("data_file")) or req.form.get("data", "").strip()


def form_id(form, field):
    try:
        return int(form.get(field, ""))
    except ValueError:
        return None


# The playground page. inputs holds the prompt, data and experiment name shown in the form; experiment is the saved
# experiment being viewed, if any; run_id is the unsaved run whose result is shown, so Save can keep it.
def render_playground(inputs, settings, result=None, error=None, experiment=None, run_id=None, response=None,
                      response2=None, notice=None):
    return render_template("playground.html", inputs=inputs, settings=settings, result=result, error=error,
                           experiment=experiment, run_id=run_id, response=response, response2=response2,
                           notice=notice, model=model, active_nav="playground")


# The site's only login is Caddy's basic auth, which browsers also send with forms posted from other sites, so
# reject cross-site POSTs (they could delete or overwrite saved experiments)
@main.before_request
def reject_cross_site_posts():
    if request.method != "POST":
        return
    site = request.headers.get("Sec-Fetch-Site")
    if site is not None:
        if site not in ("same-origin", "none"):
            abort(403)
        return
    origin = request.headers.get("Origin")
    if origin and origin.split("://", 1)[-1] != request.host:
        abort(403)


# Number of saved experiments, for the sidebar
@main.app_context_processor
def saved_count():
    return {"saved_count": experiments.count_experiments()}


@main.route("/", methods=["GET", "POST"])
def home():
    response = None
    response2 = None
    result = None
    error = None
    run_id = None
    settings = dict(DEFAULT_SETTINGS)
    inputs = {"prompt": "", "data": "", "name": ""}

    if request.method == "POST":
        # prompt from user
        prompt = request.form.get("prompt", "").strip()

        # data from user. Text from uploaded files goes back in the text box, so Save and re-runs keep it.
        try:
            data = form_data(request)
        except UploadError as e:
            data, error = request.form.get("data", "").strip(), str(e)

        settings = form_settings(request.form)
        inputs = {"prompt": prompt, "data": data, "name": request.form.get("experiment_name", "").strip()}

        # prompt hardening response w/ Ollama, commented out because its kind of slow and we want to focus on the sanitization engine for now
        # response = chat(
        #     model=model,
        #     messages=[{'role': 'user', 'content': harden_prompt(prompt, data)}],
        # )

        # response2 = chat(
        #     model=model,
        #     messages=[{'role': 'user', 'content': " ".join([prompt, data])}],
        # )

        if error is None and not (prompt and data):
            error = "Enter a prompt and some source data (text or a file), then run the experiment."
        if error is None:
            try:
                result = run_experiment(prompt, data, settings)
                run_id = experiments.record_run(prompt, data, settings, result)
            except LLMUnavailable:
                error = "Could not reach the LLM. Check that Ollama is running, then submit again."

        print(response)

    # Re-running a saved experiment keeps editing it, so Save updates it instead of creating another
    experiment = experiments.get_experiment(form_id(request.form, "experiment_id")) if request.method == "POST" else None

    return render_playground(inputs, settings, result=result, error=error, experiment=experiment, run_id=run_id,
                             response=response, response2=response2)


@main.route("/experiments")
def experiment_list():
    saved = experiments.list_experiments()
    for experiment in saved:
        experiment["mitigations_on"] = sum(on for name, on in experiment["settings"].items() if name.startswith("mit_"))
    return render_template("experiments.html", experiments=saved, model=model, active_nav="experiments")


@main.route("/guide")
def guide():
    return render_template("guide.html", model=model, active_nav="guide")


@main.route("/experiments/<int:experiment_id>")
def view_experiment(experiment_id):
    experiment = experiments.get_experiment(experiment_id)
    if experiment is None:
        abort(404)
    inputs = {"prompt": experiment["prompt"], "data": experiment["data"], "name": experiment["name"]}
    settings = {**DEFAULT_SETTINGS, **experiment["settings"]}
    notice = None
    if request.args.get("expired"):
        notice = (f"The results on the page had expired (unsaved runs are kept for {experiments.UNSAVED_RUN_DAYS} day), "
                  "so this was saved as a draft. Run it again to save results.")
    return render_playground(inputs, settings, result=experiment["result"], experiment=experiment, notice=notice)


# Save the form (the Save button posts the same form here), with the shown run's results if the inputs still match
@main.route("/experiments/save", methods=["POST"])
def save_experiment():
    name = request.form.get("experiment_name", "").strip()[:NAME_LENGTH] or "Untitled experiment"
    try:
        data = form_data(request)
    except UploadError as e:
        inputs = {"prompt": request.form.get("prompt", "").strip(), "data": request.form.get("data", "").strip(),
                  "name": request.form.get("experiment_name", "").strip()}
        return render_playground(inputs, form_settings(request.form), error=str(e),
                                 experiment=experiments.get_experiment(form_id(request.form, "experiment_id")))
    experiment_id, run_expired = experiments.save_experiment(
        name,
        request.form.get("prompt", "").strip(),
        data,
        form_settings(request.form),
        run_id=form_id(request.form, "run_id"),
        experiment_id=form_id(request.form, "experiment_id"),
    )
    expired = {"expired": 1} if run_expired else {}
    return redirect(url_for("main.view_experiment", experiment_id=experiment_id, **expired))


@main.route("/experiments/<int:experiment_id>/delete", methods=["POST"])
def delete_experiment(experiment_id):
    experiments.delete_experiment(experiment_id)
    return redirect(url_for("main.experiment_list"))
