import logging

from flask import Blueprint, render_template


# Uncomment following line to print DEBUG logs
#  logging.basicConfig(encoding='utf-8', level=logging.DEBUG)

bp = Blueprint('benchmark_history', __name__, url_prefix='/benchmark-history')


# ROUTES
@bp.route('/', methods=('GET',))
def index():
    """Benchmark History tab index page."""
    return render_template("tabs/benchmark_history.html")
