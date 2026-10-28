import pytest


# Web app tests save experiments to a throwaway database instead of code/instance/
@pytest.fixture(autouse=True)
def experiments_db(tmp_path, monkeypatch):
    path = tmp_path / "experiments.db"
    monkeypatch.setenv("EXPERIMENTS_DB", str(path))
    return path
