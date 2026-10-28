import os

from flask import Flask


# EXPERIMENTS_DB is where saved experiments are kept (see experiments.py). In Docker it must be on a volume, or
# rebuilding the container deletes them; docker-compose.yml sets it.
def create_app(test_config=None):
    app = Flask(__name__)
    app.config["EXPERIMENTS_DB"] = os.environ.get("EXPERIMENTS_DB") or os.path.join(app.instance_path, "experiments.db")
    if test_config:
        app.config.update(test_config)

    from . import experiments
    experiments.init_app(app)

    from .routes import main
    app.register_blueprint(main)

    return app
