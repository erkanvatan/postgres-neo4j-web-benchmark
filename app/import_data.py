import csv
from datetime import datetime
import logging
from types import LambdaType

from flask import Blueprint, flash, g, redirect, render_template, request, url_for
import psycopg

from app.db import get_neo4j, get_psql, init_neo4j_command, init_psql


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
                if g.get("is_import_psql_disabled"):
                    flash("PostgreSQL tables are not empty. You have to drop them before importing.", "warning")
                else:
                    if f.get("is_import_psql", default="") == "on":
                        import_to_psql()
                        g.is_import_psql_disabled = True

                    if f.get("is_import_neo4j", default="") == "on":
                        import_to_neo4j()
                        g.is_import_neo4j_disabled = True
                    flash("Import finished!", "info")
            elif f.get("drop_button") is not None:
                if g.get("is_import_neo4j_disabled"):
                    flash("Neo4j tables are not empty. You have to drop them before importing.", "warning")
                else:
                    if f.get("is_import_psql", default="") == "on":
                        try:
                            init_psql()
                            g.is_import_psql_disabled = False
                        except psycopg.errors.ObjectInUse as e:
                            flash(e, "warning")

                    if f.get("is_import_neo4j", default="") == "on":
                        init_neo4j_command()
                        g.is_import_neo4j_disabled = False
                    flash("Drop finished!", "info")

    return render_template("tabs/import_data.html")


# Functions
def csv_to_table(cursor: psycopg.Cursor, record_parser: LambdaType, table_name: str):
    """Read rows from CSV and insert them into given database table."""
    with cursor.copy(f"COPY {table_name} FROM STDIN") as copy:
        with open(f'jars/csv/{table_name}.csv', newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter=',', quotechar='"')
            # Skip header
            reader.__next__()
            for row in reader:
                record = record_parser(row)
                copy.write_row(record)


def import_to_psql():
    """Import data into PostgreSQL database using CSV files."""
    psql = get_psql("warehouse")
    cursor = psql.cursor()

    try:
        csv_to_table(cursor, lambda x: (int(x[0]), x[1], x[2]), "customer")
        psql.commit()
    except psycopg.errors.IntegrityError:
        flash('"customer" table is not empty', "warning")
        psql.rollback()

    try:
        csv_to_table(cursor, lambda x: (int(x[0]), x[1], int(x[2]), x[3], float(x[4]), float(x[5]),
                                        True if x[6] == "true" else False), "item")
        psql.commit()
    except psycopg.errors.IntegrityError:
        flash('"item" table is not empty', "warning")
        psql.rollback()

    try:
        csv_to_table(cursor, lambda x: (int(x[0]), x[1], int(x[2])), "worktype")
        psql.commit()
    except psycopg.errors.IntegrityError:
        flash('"worktype" table is not empty', "warning")
        psql.rollback()

    try:
        csv_to_table(cursor, lambda x: (int(x[0]), int(x[1]), int(x[2]), int(x[4])), "invoice")
        psql.commit()
    except psycopg.errors.IntegrityError:
        flash('"invoice" table is not empty', "warning")
        psql.rollback()

    try:
        csv_to_table(cursor, lambda x: (int(x[0]), x[1], x[2], int(x[3])), "target")
        psql.commit()
    except psycopg.errors.IntegrityError:
        flash('"target" table is not empty', "warning")
        psql.rollback()

    try:
        csv_to_table(cursor, lambda x: (int(x[0]), x[1]), "work")
        psql.commit()
    except psycopg.errors.IntegrityError:
        flash('"work" table is not empty', "warning")
        psql.rollback()

    try:
        csv_to_table(cursor, lambda x: (int(x[0]), int(x[1])), "workinvoice")
        psql.commit()
    except psycopg.errors.IntegrityError:
        flash('"workinvoice" table is not empty', "warning")
        psql.rollback()

    try:
        csv_to_table(cursor, lambda x: (int(x[0]), int(x[1])), "worktarget")
        psql.commit()
    except psycopg.errors.IntegrityError:
        flash('"worktarget" table is not empty', "warning")
        psql.rollback()

    try:
        csv_to_table(cursor, lambda x: (int(x[0]), float(x[1]), int(x[2]), int(x[3])), "useditem")
        psql.commit()
    except psycopg.errors.IntegrityError:
        flash('"useditem" table is not empty', "warning")
        psql.rollback()

    try:
        csv_to_table(cursor, lambda x: (int(x[0]), int(x[1]), float(x[2]), int(x[3])), "workhours")
        psql.commit()
    except psycopg.errors.IntegrityError:
        flash('"workhours" table is not empty', "warning")
        psql.rollback()


def import_to_neo4j():
    """Import data into Neo4j database using CSV files."""
    print("import_neo4j")
    neo4j = get_neo4j()

    # Create "customer" label
    neo4j.execute_query("""
LOAD CSV WITH HEADERS FROM 'file:///csv/customer.csv' AS row
CREATE (:customer {id: toInteger(row.id), name: row.name, address: row.address})""", database_="neo4j")

    # Create "item" label
    neo4j.execute_query("""
LOAD CSV WITH HEADERS FROM 'file:///csv/item.csv' AS row
CREATE (:item {id: toInteger(row.id), name: row.name, balance: toInteger(row.balance),
unit: row.unit, purchaseprice: toFloat(row.purchaseprice), vat: toFloat(row.vat), removed: toBoolean(row.removed)})""",
                        database_="neo4j")

    # Create "worktype" label
    neo4j.execute_query("""
LOAD CSV WITH HEADERS FROM 'file:///csv/worktype.csv' AS row
CREATE (:worktype {id: toInteger(row.id), name: row.name, price: toInteger(row.price)})""",
                        database_="neo4j")

    # Create "invoice" label
    neo4j.execute_query("""
LOAD CSV WITH HEADERS FROM 'file:///csv/invoice.csv' AS row
CREATE (:invoice {id: toInteger(row.id), state: toInteger(row.state)})""",
                        database_="neo4j")

    # Create "target" label
    neo4j.execute_query("""
LOAD CSV WITH HEADERS FROM 'file:///csv/target.csv' AS row
CREATE (:target {id: toInteger(row.id), name: row.name, address: row.address})""",
                        database_="neo4j")

    # Create "work" label
    neo4j.execute_query("""
LOAD CSV WITH HEADERS FROM 'file:///csv/work.csv' AS row
CREATE (:work {id: toInteger(row.id), name: row.name})""",
                        database_="neo4j")

    # Create indexes for fast search
    neo4j.execute_query("CREATE INDEX invoice_pk FOR (in:invoice) ON (in.id)")
    neo4j.execute_query("CREATE INDEX customer_pk FOR (cust:customer) ON (cust.id)")
    neo4j.execute_query("CALL db.awaitIndexes()")

    # Create "PAYS" relationship from "customer" to "invoice"
    neo4j.execute_query("""
LOAD CSV WITH HEADERS FROM 'file:///csv/invoice.csv' AS row
MATCH (cust:customer {id: toInteger(row.customerid)})
MATCH (inv:invoice {id: toInteger(row.id)})
CREATE (cust)-[:PAYS]->(inv)""",
                        database_="neo4j")

    # Create indexes for fast search
    neo4j.execute_query("CREATE INDEX target_pk FOR (tar:target) ON (tar.id)", database_="neo4j")
    neo4j.execute_query("CALL db.awaitIndexes()", database_="neo4j")

    # Create "CUSTOMER_TARGET" relationship from "customer" to "target"
    neo4j.execute_query("""
LOAD CSV WITH HEADERS FROM 'file:///csv/target.csv' AS row
MATCH (cust:customer {id: toInteger(row.customerid)})
MATCH (tar:target {id: toInteger(row.id)})
CREATE (cust)-[:CUSTOMER_TARGET]->(tar)""",
                        database_="neo4j")

    #  Create indexes for fast search
    neo4j.execute_query("CREATE INDEX work_pk FOR (w:work) ON (w.id)", database_="neo4j")
    neo4j.execute_query("CALL db.awaitIndexes()", database_="neo4j")

    #  Create "WORK_INVOICE" relationship between "work" and "invoice"
    neo4j.execute_query("""
LOAD CSV WITH HEADERS FROM 'file:///csv/workinvoice.csv' AS row
MATCH (w:work {id: toInteger(row.workid)})
MATCH (inv:invoice {id: toInteger(row.invoiceid)})
CREATE (inv)-[:WORK_INVOICE]->(w)
CREATE (w)-[:WORK_INVOICE]->(inv)""",
                        database_="neo4j")

    #  Create "WORK_TARGET" relationship between "work" and "target"
    neo4j.execute_query("""
LOAD CSV WITH HEADERS FROM 'file:///csv/worktarget.csv' AS row
MATCH (w:work {id: toInteger(row.workid)})
MATCH (tar:target {id: toInteger(row.targetid)})
CREATE (w)-[:WORK_TARGET]->(tar)
CREATE (tar)-[:WORK_TARGET]->(w)""",
                        database_="neo4j")

    #  Create indexes for fast search
    neo4j.execute_query("CREATE INDEX item_pk FOR (it:item) ON (it.id)", database_="neo4j")
    neo4j.execute_query("CALL db.awaitIndexes()", database_="neo4j")

    #  Create "WORK_TARGET" relationship between "work" and "target"
    neo4j.execute_query("""
LOAD CSV WITH HEADERS FROM 'file:///csv/useditem.csv' AS row
MATCH (w:work {id: toInteger(row.workid)})
MATCH (it:item {id: toInteger(row.itemid)})
CREATE (w)-[:USED_ITEM {amount: toInteger(row.amount),
discount: toFloat(row.discount)} ]->(it)
CREATE (it)-[:USED_ITEM {amount: toInteger(row.amount),
discount: toFloat(row.discount)} ]->(w)""",
                        database_="neo4j")

    #  Create indexes for fast search
    neo4j.execute_query("CREATE INDEX worktype_pk FOR (wt:worktype) ON (wt.id)", database_="neo4j")
    neo4j.execute_query("CALL db.awaitIndexes()", database_="neo4j")

    #  Create "WORK_TARGET" relationship between "work" and "target"
    neo4j.execute_query("""
LOAD CSV WITH HEADERS FROM 'file:///csv/workhours.csv' AS row
MATCH (w:work {id: toInteger(row.workid)})
MATCH (wt:worktype {id: toInteger(row.worktypeid)})
CREATE (w)-[:WORKHOURS {hours: toInteger(row.hours),
discount: toFloat(row.discount)} ]->(wt)
CREATE (wt)-[:WORKHOURS {hours: toInteger(row.hours),
discount: toFloat(row.discount)} ]->(w)""",
                        database_="neo4j")

    # Drop created indexes
    neo4j.execute_query("""
DROP INDEX customer_pk IF EXISTS;
DROP INDEX invoice_pk IF EXISTS;
DROP INDEX item_pk IF EXISTS;
DROP INDEX target_pk IF EXISTS;
DROP INDEX work_pk IF EXISTS;
DROP INDEX worktype_pk IF EXISTS;""", databaes_="neo4j")
