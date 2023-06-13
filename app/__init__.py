import os

from flask import Flask, flash
from flask_session import Session


def create_app(test_config=None):
    """Create and return Flask instance"""
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    # Set config values
    app.config.from_mapping(
        SECRET_KEY='dev',
        SESSION_TYPE='filesystem',
        SESSION_PERMANENT=True,
        SESSION_COOKIE_HTTPONLY=True,
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    # Initialize session
    Session(app)

    # Initialize app with database commands
    from . import db
    db.init_app(app)

    # Register blueprints
    from . import (index, import_data, run_benchmark, benchmark_history)
    app.register_blueprint(index.bp)
    app.register_blueprint(import_data.bp)
    app.register_blueprint(run_benchmark.bp)
    app.register_blueprint(benchmark_history.bp)
    # Make index the root
    app.add_url_rule('/', endpoint='index')

    # Define jinja2 functions
    @app.context_processor
    def jinja_flash_message():
        def flash_message(str, type):
            """Flash messages inside jinja templates"""
            flash(str, type)
        return dict(flash_message=flash_message)

    return app
