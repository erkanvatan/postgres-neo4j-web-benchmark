import logging

from flask import Blueprint, render_template


# Uncomment following line to print DEBUG logs
#  logging.basicConfig(encoding='utf-8', level=logging.DEBUG)

bp = Blueprint('run_benchmark', __name__, url_prefix='/run-benchmark')


# ROUTES
@bp.route('/', methods=('GET',))
def index():
    """Run Benchmark tab index page."""
    return render_template("tabs/run_benchmark.html")
