import csv
from datetime import datetime
import logging
from types import LambdaType

from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from neo4j import exceptions
import psycopg

from app.db import get_neo4j, get_psql, init_neo4j, init_psql


# Uncomment following line to print DEBUG logs
#  logging.basicConfig(encoding='utf-8', level=logging.DEBUG)

bp = Blueprint('import_data', __name__, url_prefix='/import-data')


# ROUTES
@bp.route('/', methods=('GET', 'POST'))
def index():
    """Import Data tab index page."""

    if request.method == "POST":
        f = request.form

        if f.get("is_import_psql") is None and f.get("is_import_neo4j") is None:
            flash("You must at least check one box", "warning")
        else:
            if f.get("import_button") is not None:
                db_name = f.get("select_database")
                if db_name not in PSQL_TABLES:
                    flash("You must select a database", "warning")
                else:
                    is_ok = True
                    try:
                        if f.get("is_import_psql", default="") == "on":
                            is_ok = import_to_psql(db_name, PSQL_TABLES[db_name]) and is_ok
                        if f.get("is_import_neo4j", default="") == "on":
                            NEO4J_IMPORTERS[db_name]()
                    except exceptions.ConstraintError:
                        flash("Neo4j database is not empty.", "warning")
                        is_ok = False
                    except FileNotFoundError:
                        flash(f'CSV files for "{db_name}" not found. Run "task generate" first.', "warning")
                        is_ok = False
                    except exceptions.ClientError as e:
                        flash(e.message, "warning")
                        is_ok = False

                    if is_ok:
                        flash("Import finished!", "info")
            elif f.get("drop_button") is not None:
                if f.get("is_import_psql", default="") == "on":
                    try:
                        init_psql()
                    except psycopg.errors.ObjectInUse as e:
                        flash(e, "warning")

                if f.get("is_import_neo4j", default="") == "on":
                    init_neo4j()

                flash("Drop finished!", "info")

    return render_template("tabs/import_data.html")


# Functions
def csv_to_table(cursor: psycopg.Cursor, record_parser: LambdaType, table_name: str, db_name: str):
    """Read rows from CSV and insert them into given database table."""
    with cursor.copy(f"COPY {table_name} FROM STDIN") as copy:
        with open(f'data/{db_name}/{table_name}.csv', newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter=',', quotechar='"')
            # Skip header
            reader.__next__()
            for row in reader:
                record = record_parser(row)
                copy.write_row(record)


def import_to_psql(db_name: str, tables: list) -> bool:
    """Import CSV files into the given PostgreSQL database, return False if a table was not empty."""
    psql = get_psql(db_name)
    cursor = psql.cursor()
    is_ok = True

    for table_name, record_parser in tables:
        try:
            csv_to_table(cursor, record_parser, table_name, db_name)
            psql.commit()
        except psycopg.errors.IntegrityError:
            flash(f'"{table_name}" table is not empty', "warning")
            psql.rollback()
            is_ok = False

    return is_ok


def import_to_neo4j_warehouse():
    """Import data into Neo4j "warehouse" database using CSV files."""
    neo4j = get_neo4j()

    # Create "customer" label
    neo4j.execute_query("""
LOAD CSV WITH HEADERS FROM 'file:///warehouse/customer.csv' AS row
CREATE (:customer {id: toInteger(row.id), name: row.name, address: row.address})""", database_="neo4j")

    # Create "item" label
    neo4j.execute_query("""
LOAD CSV WITH HEADERS FROM 'file:///warehouse/item.csv' AS row
CREATE (:item {id: toInteger(row.id), name: row.name, balance: toInteger(row.balance),
unit: row.unit, purchaseprice: toFloat(row.purchaseprice), vat: toFloat(row.vat), removed: toBoolean(row.removed)})""",
                        database_="neo4j")

    # Create "worktype" label
    neo4j.execute_query("""
LOAD CSV WITH HEADERS FROM 'file:///warehouse/worktype.csv' AS row
CREATE (:worktype {id: toInteger(row.id), name: row.name, price: toInteger(row.price)})""",
                        database_="neo4j")

    # Create "invoice" label
    neo4j.execute_query("""
LOAD CSV WITH HEADERS FROM 'file:///warehouse/invoice.csv' AS row
CREATE (:invoice {id: toInteger(row.id), state: toInteger(row.state)})""",
                        database_="neo4j")

    # Create "target" label
    neo4j.execute_query("""
LOAD CSV WITH HEADERS FROM 'file:///warehouse/target.csv' AS row
CREATE (:target {id: toInteger(row.id), name: row.name, address: row.address})""",
                        database_="neo4j")

    # Create "work" label
    neo4j.execute_query("""
LOAD CSV WITH HEADERS FROM 'file:///warehouse/work.csv' AS row
CREATE (:work {id: toInteger(row.id), name: row.name})""",
                        database_="neo4j")

    # Create indexes for fast search
    neo4j.execute_query("CREATE CONSTRAINT customer_pk IF NOT EXISTS FOR (cust:customer) REQUIRE cust.id IS UNIQUE")
    neo4j.execute_query("CREATE CONSTRAINT item_pk IF NOT EXISTS FOR (it:item) REQUIRE it.id IS UNIQUE")
    neo4j.execute_query("CREATE CONSTRAINT worktype_pk IF NOT EXISTS FOR (wt:worktype) REQUIRE wt.id IS UNIQUE")
    neo4j.execute_query("CREATE CONSTRAINT invoice_pk IF NOT EXISTS FOR (in:invoice) REQUIRE in.id IS UNIQUE")
    neo4j.execute_query("CREATE CONSTRAINT target_pk IF NOT EXISTS FOR (tar:target) REQUIRE tar.id IS UNIQUE")
    neo4j.execute_query("CREATE CONSTRAINT work_pk IF NOT EXISTS FOR (w:work) REQUIRE w.id IS UNIQUE")
    neo4j.execute_query("CALL db.awaitIndexes()")

    # Create "PAYS" relationship from "customer" to "invoice"
    neo4j.execute_query("""
LOAD CSV WITH HEADERS FROM 'file:///warehouse/invoice.csv' AS row
MATCH (cust:customer {id: toInteger(row.customerid)})
MATCH (inv:invoice {id: toInteger(row.id)})
CREATE (cust)-[:PAYS]->(inv)""",
                        database_="neo4j")

    # Create "CUSTOMER_TARGET" relationship from "customer" to "target"
    neo4j.execute_query("""
LOAD CSV WITH HEADERS FROM 'file:///warehouse/target.csv' AS row
MATCH (cust:customer {id: toInteger(row.customerid)})
MATCH (tar:target {id: toInteger(row.id)})
CREATE (cust)-[:CUSTOMER_TARGET]->(tar)""",
                        database_="neo4j")

    #  Create "WORK_INVOICE" relationship between "work" and "invoice"
    neo4j.execute_query("""
LOAD CSV WITH HEADERS FROM 'file:///warehouse/workinvoice.csv' AS row
MATCH (w:work {id: toInteger(row.workid)})
MATCH (inv:invoice {id: toInteger(row.invoiceid)})
CREATE (w)-[:WORK_INVOICE]->(inv)""",
                        database_="neo4j")

    #  Create "WORK_TARGET" relationship between "work" and "target"
    neo4j.execute_query("""
LOAD CSV WITH HEADERS FROM 'file:///warehouse/worktarget.csv' AS row
MATCH (w:work {id: toInteger(row.workid)})
MATCH (tar:target {id: toInteger(row.targetid)})
CREATE (w)-[:WORK_TARGET]->(tar)""",
                        database_="neo4j")

    #  Create "USED_ITEM" relationship between "work" and "item"
    neo4j.execute_query("""
LOAD CSV WITH HEADERS FROM 'file:///warehouse/useditem.csv' AS row
MATCH (w:work {id: toInteger(row.workid)})
MATCH (it:item {id: toInteger(row.itemid)})
CREATE (w)-[:USED_ITEM {amount: toInteger(row.amount),
discount: toFloat(row.discount)} ]->(it)""",
                        database_="neo4j")

    #  Create "WORKHOURS" relationship between "work" and "worktype"
    neo4j.execute_query("""
LOAD CSV WITH HEADERS FROM 'file:///warehouse/workhours.csv' AS row
MATCH (w:work {id: toInteger(row.workid)})
MATCH (wt:worktype {id: toInteger(row.worktypeid)})
CREATE (w)-[:WORKHOURS {hours: toInteger(row.hours),
discount: toFloat(row.discount)} ]->(wt)""",
                        database_="neo4j")


def import_to_neo4j_university():
    """Import data into Neo4j "university" database using CSV files."""
    neo4j = get_neo4j()

    # Create "course" label
    neo4j.execute_query("""
LOAD CSV WITH HEADERS FROM 'file:///university/course.csv' AS row
CREATE (:course {course_id: row.course_id, title: row.title})""",
                        database_="neo4j")

    # Create "student" label
    neo4j.execute_query("""
LOAD CSV WITH HEADERS FROM 'file:///university/student.csv' AS row
CREATE (:student {student_id: row.student_id, name: row.name})""",
                        database_="neo4j")

    #  Create indexes for fast search
    neo4j.execute_query("CREATE CONSTRAINT student_pk IF NOT EXISTS FOR (st:student) REQUIRE st.student_id IS UNIQUE")
    neo4j.execute_query("CREATE CONSTRAINT course_pk IF NOT EXISTS FOR (co:course) REQUIRE co.course_id IS UNIQUE")
    neo4j.execute_query("CALL db.awaitIndexes()")

    #  Create "TAKES" relationship between "student" and "course"
    neo4j.execute_query("""
LOAD CSV WITH HEADERS FROM 'file:///university/takes.csv' AS row
MATCH (st:student {student_id: row.student_id})
MATCH (co:course {course_id: row.course_id})
CREATE (st)-[:TAKES {year: row.year, semester: row.semester, grade: toFloat(row.grade)} ]->(co)""",
                        database_="neo4j")

    #  Create "PREREQ" relationship between "course" and "course"
    neo4j.execute_query("""
LOAD CSV WITH HEADERS FROM 'file:///university/prereq.csv' AS row
MATCH (co:course {course_id: row.course_id})
MATCH (pre:course {course_id: row.prereq_id})
CREATE (co)-[:PREREQ]->(pre)""",
                        database_="neo4j")


PSQL_TABLES = {
    "warehouse": [
        ("customer", lambda x: (int(x[0]), x[1], x[2])),
        ("item", lambda x: (int(x[0]), x[1], int(x[2]), x[3], float(x[4]), float(x[5]), x[6] == "true")),
        ("worktype", lambda x: (int(x[0]), x[1], int(x[2]))),
        ("invoice", lambda x: (int(x[0]), int(x[1]), int(x[2]), int(x[4]))),
        ("target", lambda x: (int(x[0]), x[1], x[2], int(x[3]))),
        ("work", lambda x: (int(x[0]), x[1])),
        ("workinvoice", lambda x: (int(x[0]), int(x[1]))),
        ("worktarget", lambda x: (int(x[0]), int(x[1]))),
        ("useditem", lambda x: (int(x[0]), float(x[1]), int(x[2]), int(x[3]))),
        ("workhours", lambda x: (int(x[0]), int(x[1]), float(x[2]), int(x[3]))),
    ],
    "university": [
        ("course", lambda x: (x[0], x[1])),
        ("student", lambda x: (x[0], x[1])),
        ("takes", lambda x: (x[0], x[1], x[2], x[3], float(x[4]))),
        ("prereq", lambda x: (x[0], x[1])),
    ],
}

NEO4J_IMPORTERS = {
    "warehouse": import_to_neo4j_warehouse,
    "university": import_to_neo4j_university,
}
