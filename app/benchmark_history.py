import logging
from statistics import median

from flask import Blueprint, flash, render_template
import psycopg
from psycopg.rows import dict_row

from app.db import get_psql


# Uncomment following line to print DEBUG logs
#  logging.basicConfig(encoding='utf-8', level=logging.DEBUG)

bp = Blueprint('benchmark_history', __name__, url_prefix='/benchmark-history')


# ROUTES
@bp.route('/', methods=('GET',))
def index():
    """Benchmark History tab index page."""
    logs = []
    rows = []

    try:
        psql = get_psql()
        psql.row_factory = dict_row
        logs = psql.execute("SELECT * FROM benchmark_log ORDER BY benchmark_log_id DESC").fetchall()
        psql.commit()

        for log in logs:
            row = {}
            row["benchmark_log_id"] = log["benchmark_log_id"]
            row["iteration_count"] = log["iteration_count"]
            row["psql_query"] = log["psql_query"]
            row["neo4j_query"] = log["neo4j_query"]
            row["psql_nrows"] = log["psql_nrows"][0]
            row["neo4j_nrows"] = log["neo4j_nrows"][0]

            for db in ("psql", "neo4j"):
                runtimes = log[f"{db}_runtimes"]
                row[f"{db}_runtimes"] = ", ".join(map(str, runtimes))
                row[f"{db}_min"] = min(runtimes)
                row[f"{db}_median"] = round(median(runtimes), 2)
                row[f"{db}_max"] = max(runtimes)

            rows.append(row)

    except psycopg.errors.Error as e:
        flash(e, "warning")

    return render_template("tabs/benchmark_history.html", rows=rows)
