import logging

from flask import Blueprint, render_template


# Uncomment following line to print DEBUG logs
#  logging.basicConfig(encoding='utf-8', level=logging.DEBUG)

bp = Blueprint('import_data', __name__, url_prefix='/import-data')


# ROUTES
@bp.route('/', methods=('GET',))
def index():
    """Import Data tab index page."""
    return render_template("tabs/import_data.html")
