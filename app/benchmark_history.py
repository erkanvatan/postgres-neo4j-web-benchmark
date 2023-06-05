import logging

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
        logs = psql.execute("SELECT * FROM benchmark_log").fetchall()
        psql.commit()

        for log in logs:
            row = {}
            row["benchmark_log_id"] = log["benchmark_log_id"]
            row["iteration_count"] = log["iteration_count"]
            row["psql_query"] = log["psql_query"]
            row["neo4j_query"] = log["neo4j_query"]
            row["psql_nrows"] = log["psql_nrows"][0]
            row["neo4j_nrows"] = log["neo4j_nrows"][0]

            psql_runtimes = log["psql_runtimes"]
            row["psql_runtimes"] = ','.join(map(str, psql_runtimes))

            sort = sorted(psql_runtimes)
            sort = sort[1: -1]
            row["psql_min"] = sort[0]
            row["psql_max"] = sort[-1]
            row["psql_avg"] = sum(sort) / len(sort)

            neo4j_runtimes = log["neo4j_runtimes"]
            row["neo4j_runtimes"] = ','.join(map(str, neo4j_runtimes))
            sort = sorted(neo4j_runtimes)
            sort = sort[1: -1]
            row["neo4j_min"] = sort[0]
            row["neo4j_max"] = sort[-1]
            row["neo4j_avg"] = sum(sort) / len(sort)

            rows.append(row)

    except psycopg.errors.Error as e:
        flash(e, "warning")

    return render_template("tabs/benchmark_history.html", rows=rows)
