import os

from quart import Quart


def create_app():
    app = Quart(__name__)
    app.config.from_pyfile("../config.py")
    app.config["REMANDZANA_FEEDBACK_DIRECTORY"] = os.path.join(
        app.root_path,
        app.config["REMANDZANA_FEEDBACK_DIRECTORY"]
    )
    app.config["REMANDZANA_AHMIA_LOCATION"] = os.path.join(
        app.root_path,
        app.config["REMANDZANA_AHMIA_LOCATION"]
    )

    from .lobbies import ALL_LOBBIES
    app.lobbies = ALL_LOBBIES

    from .main import bp as main_bp
    from .chat import bp as chat_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(chat_bp)

    from .models.metrics import Metrics
    app.metrics = Metrics(
        app.config.get("REMANDZANA_METRICS_PERIOD", 86400),
        app.config.get("REMANDZANA_METRICS_COOLDOWN", 60)
    )

    @app.after_request
    def cache_control(response):
        content_type = response.headers.get("Content-Type", "")
        content_type = content_type.split(";", maxsplit=1)[0]
        if content_type == "text/css":
            response.cache_control.public = True
            response.cache_control.immutable = True
        return response

    return app
