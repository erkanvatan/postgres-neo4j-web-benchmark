import csv
from datetime import datetime
import logging
from types import LambdaType

from flask import Blueprint, flash, g, redirect, render_template, request, url_for
import psycopg

from app.db import get_neo4j, get_psql


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
            if f.get("is_import_psql", default="") == "on":
                import_to_psql()

            if f.get("is_import_neo4j", default="") == "on":
                import_to_neo4j()

            flash("Import finished!", "info")

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
                                        1 if x[6] == "true" else 0), "item")
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
        csv_to_table(cursor, lambda x: (int(x[0]), int(x[1]), int(x[2]),
                                        datetime.strptime(x[3], '%d-%b-%Y').date(), int(x[4])), "invoice")
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

    neo4j.execute_query("""
    LOAD CSV WITH HEADERS FROM 'file:///csv/customer.csv' AS row
    MERGE (c:Customer {id: row.id, name: row.name, address: row.address});
                        """)
