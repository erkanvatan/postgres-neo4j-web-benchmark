import logging
import time

from flask import (
    Blueprint,
    abort,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
import neo4j.exceptions
import psycopg
from psycopg.rows import dict_row

from app.db import get_neo4j, get_psql


# Uncomment following line to print DEBUG logs
#  logging.basicConfig(encoding='utf-8', level=logging.DEBUG)

bp = Blueprint('run_benchmark', __name__, url_prefix='/run-benchmark')


# ROUTES
@bp.route('/get-query/<int:saved_query_id>')
def get_query(saved_query_id: int):
    """Find query according to the given id in GET request,
    return JSON object containing the query."""
    psql = get_psql()
    psql.row_factory = dict_row

    try:
        query = psql.execute("SELECT * FROM saved_query WHERE saved_query_id = %s", (saved_query_id,)).fetchone()
        psql.commit()

        return jsonify(query)
    except psycopg.errors.Error as e:
        print(e)
        abort(404)


@bp.route('/', methods=('GET', 'POST'))
def index():
    """Run Benchmark tab index page."""
    is_error = False
    saved_queries = []

    try:
        psql = get_psql()
        psql.row_factory = dict_row
        queries = psql.execute("SELECT * FROM saved_query").fetchall()
        psql.commit()

        for query in queries:
            row = {}
            row["saved_query_id"] = query["saved_query_id"]
            row["selected_database"] = query["selected_database"]
            row["psql_query"] = query["psql_query"]
            row["neo4j_query"] = query["neo4j_query"]
            row["iteration_count"] = query["iteration_count"]
            saved_queries.append(row)

    except psycopg.errors.Error as e:
        flash(e, "warning")
        is_error = True

    if request.method == "POST":
        f = request.form

        session["psql_query"] = f["psql_query"]
        session["neo4j_query"] = f["neo4j_query"]
        if f.get("select_database") is None or f.get("select_database") == "Select Database":
            flash("You must select a database", "warning")
            is_error = True

        if f.get("select_database") == "warehouse":
            session["is_default_selected"] = ""
            session["is_warehouse_selected"] = "selected"
            session["is_university_selected"] = ""
        elif f.get("select_database") == "university":
            session["is_default_selected"] = ""
            session["is_warehouse_selected"] = ""
            session["is_university_selected"] = "selected"
        else:
            flash("Unknown database option.", "warning")
            is_error = True

        if not f["psql_query"]:
            flash("You must enter a PostgreSQL query.", "warning")
            is_error = True

        if not f["neo4j_query"]:
            flash("You must enter a Neo4j query.", "warning")
            is_error = True

        if f.get("save_button") is not None:
            try:
                psql = get_psql()
                psql.row_factory = dict_row

                psql.execute("""INSERT INTO saved_query(selected_database, psql_query, neo4j_query, iteration_count)
                             VALUES (%s, %s, %s, %s)""", (f["select_database"], f["psql_query"], f["neo4j_query"],
                                                          f["iteration_count"]))
                psql.commit()
                return redirect(url_for("run_benchmark.index"))

            except psycopg.errors.Error as e:
                flash(e, "warning")
                is_error = True

        if not is_error:

            iteration_count = int(f["iteration_count"])
            try:
                psql_runtimes, psql_nrows = measure_query_time_sql(f["psql_query"],
                                                                   f["select_database"], iteration_count)
                neo4j_runtimes, neo4j_nrows = measure_query_time_neo4j(f["neo4j_query"], "neo4j", iteration_count)

                psql = get_psql()
                psql.execute("""INSERT INTO benchmark_log (iteration_count, psql_query, psql_runtimes, psql_nrows,
                                                           neo4j_query, neo4j_runtimes, neo4j_nrows)
                             VALUES (%s, %s, %s, %s, %s, %s, %s)""", (iteration_count, f["psql_query"], psql_runtimes,
                                                                      psql_nrows, f["neo4j_query"], neo4j_runtimes,
                                                                      neo4j_nrows))
                psql.commit()

                flash("Benchmark finished!", "info")
            except psycopg.Error as e:
                flash(e, "warning")
            except (neo4j.exceptions.ClientError, neo4j.exceptions.ConstraintError, neo4j.exceptions.CypherSyntaxError,
                    neo4j.exceptions.DatabaseError, neo4j.exceptions.DriverError, neo4j.exceptions.Forbidden,
                    neo4j.exceptions.Neo4jError, neo4j.exceptions.CypherTypeError) as e:
                flash(e, "warning")

    return render_template("tabs/run_benchmark.html", saved_queries=saved_queries)


def measure_query_time_sql(sql_query: str, db_name: str, iteration_count: int) -> tuple:
    runtimes = []
    nrows = []

    psql = get_psql(db_name)

    for i in range(iteration_count):
        print("PSQL Query Iteration: ", i)
        start_time_sec = time.time()

        res = psql.execute(sql_query).fetchall()
        psql.commit()

        end_time_sec = time.time()

        runtimes.append(round((end_time_sec - start_time_sec) * 1000))
        nrows.append(len(res))

    return (runtimes, nrows)


def measure_query_time_neo4j(neo4j_query: str, db_name: str, iteration_count: int) -> tuple:
    runtimes = []
    nrows = []

    neo4j = get_neo4j()

    for i in range(iteration_count):
        print("Neo4j Query Iteration: ", i)
        records, summary, _ = neo4j.execute_query(neo4j_query, database_=db_name)

        runtimes.append(summary.result_consumed_after)
        nrows.append(len(records))

    return (runtimes, nrows)
