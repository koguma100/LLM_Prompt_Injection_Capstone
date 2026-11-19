import matplotlib
import pytest

# Plots are only saved to files, so draw them without a GUI. On Windows the default Tk backend sometimes fails to
# start ("Can't find a usable init.tcl"), which made run_eval tests fail at random.
matplotlib.use("Agg")


# Web app tests save experiments to a throwaway database instead of code/instance/
@pytest.fixture(autouse=True)
def experiments_db(tmp_path, monkeypatch):
    path = tmp_path / "experiments.db"
    monkeypatch.setenv("EXPERIMENTS_DB", str(path))
    return path
