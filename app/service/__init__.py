from celery import Celery
from . import celeryconfig
from flask import Flask
from flask_cors import CORS

celery = Celery(__name__)
celery.config_from_object(celeryconfig)

def create_app():
    app = Flask(__name__)
    CORS(app, expose_headers=["content-disposition"])
    celery.conf.update(app.config)

    from . import (predict)
    from . import (status)
    app.register_blueprint(predict.bp)
    app.register_blueprint(status.bp)

    return app


