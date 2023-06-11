import logging
import time

from flask import Blueprint, flash, render_template, request, session
import neo4j.exceptions
import psycopg

from app.db import get_neo4j, get_psql


# Uncomment following line to print DEBUG logs
#  logging.basicConfig(encoding='utf-8', level=logging.DEBUG)

bp = Blueprint('run_benchmark', __name__, url_prefix='/run-benchmark')


# ROUTES
@bp.route('/', methods=('GET', 'POST'))
def index():
    """Run Benchmark tab index page."""
    is_error = False

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

    return render_template("tabs/run_benchmark.html")


def measure_query_time_sql(sql_query: str, db_name: str, iteration_count: int) -> tuple:
    runtimes = []
    nrows = []

    psql = get_psql(db_name)

    for i in range(iteration_count):
        start_time_sec = time.time()

        res = psql.execute(sql_query).fetchall()

        end_time_sec = time.time()

        runtimes.append(round((end_time_sec - start_time_sec) * 1000))
        nrows.append(len(res))

    return (runtimes, nrows)


def measure_query_time_neo4j(neo4j_query: str, db_name: str, iteration_count: int) -> tuple:
    runtimes = []
    nrows = []

    neo4j = get_neo4j()

    for i in range(iteration_count):
        #  start_time_sec = time.time()

        records, summary, keys = neo4j.execute_query(neo4j_query, database_=db_name)

        #  end_time_sec = time.time()

        #  runtimes.append(round((end_time_sec - start_time_sec) * 1000))
        print(summary.result_available_after)
        print(summary.result_consumed_after)
        runtimes.append(summary.result_consumed_after)

        nrows.append(len(records))

    return (runtimes, nrows)
