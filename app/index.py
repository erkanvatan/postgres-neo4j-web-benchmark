import logging

from flask import Blueprint, render_template


# Uncomment following line to print DEBUG logs
#  logging.basicConfig(encoding='utf-8', level=logging.DEBUG)

bp = Blueprint('index', __name__)


# ROUTES
@bp.route('/', methods=('GET',))
def index():
    """Website index page."""
    return render_template("index.html")
