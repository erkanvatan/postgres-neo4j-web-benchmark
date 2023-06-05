import click
from flask import current_app, g
from flask.cli import with_appcontext
import psycopg
from neo4j import GraphDatabase


def get_psql(dbname: str = None) -> psycopg.Connection:
    """Connect to given PostgreSQL database and return connection."""

    conn_parameters = {"host": current_app.config["PSQL_HOST"], "dbname": current_app.config["PSQL_DB_NAME"],
                       "user": current_app.config["PSQL_DB_USER"], "password": current_app.config["PSQL_DB_PASSWORD"],
                       "port": current_app.config["PSQL_PORT"]}
    if dbname is not None:
        conn_parameters["dbname"] = dbname

    if 'psql' not in g:
        g.psql = {}

    if conn_parameters["dbname"] not in g.psql:
        # `g` object is used to store connection for multiple access to a data
        # during a request
        g.psql[conn_parameters["dbname"]] = psycopg.connect(**conn_parameters)

    return g.psql[conn_parameters["dbname"]]


def get_neo4j():
    """Connect to Neo4j graph database and return connection."""
    if "neo4j" not in g:
        host = current_app.config["NEO4J_HOST"]
        port = current_app.config["NEO4J_PORT"]
        user = current_app.config["NEO4J_DB_USER"]
        password = current_app.config["NEO4J_DB_PASSWORD"]

        g.neo4j = GraphDatabase.driver(f"bolt:/{host}/:{port}",
                                       auth=(user, password))
    g.neo4j.verify_connectivity()

    return g.neo4j


def close_db(e=None):
    """Close database connections if they exist."""
    psql_dbs = g.pop('psql', None)
    neo4j = g.pop('neo4j', None)

    if psql_dbs is not None:
        for value in psql_dbs.values():
            value.close()

    if neo4j is not None:
        neo4j.close()


def import_sql(filepath: str, dbname: str = 'psqlvsneo4j'):
    """Execute sql statements from given file."""
    psql = get_psql(dbname=dbname)

    with current_app.open_resource(filepath) as f:
        psql.execute(f.read().decode('utf8'))
        psql.commit()


def init_psql():
    """Drop and recreate tables in PostgreSQL."""
    # Truncate databases
    psql = get_psql()
    # Autocommit is needed for drop database and create database commands
    psql.autocommit = True
    psql.execute("DROP DATABASE IF EXISTS psqlvsneo4j")
    psql.execute("CREATE DATABASE psqlvsneo4j")
    psql.execute("DROP DATABASE IF EXISTS testdata")
    psql.execute("CREATE DATABASE testdata")
    psql.execute("DROP DATABASE IF EXISTS warehouse")
    psql.execute("CREATE DATABASE warehouse")
    psql.autocommit = False

    # Initialize databases
    import_sql('database/init_psqlvsneo4j.sql')
    import_sql('database/init_warehouse.sql', 'warehouse')
    import_sql('database/init_testdata.sql', 'testdata')


@click.command('init-psql')
@with_appcontext
def init_psql_command():
    """Drop and recreate tables in PostgreSQL."""
    init_psql()
    click.echo('Initialized "psqlvsneo4j", "testdata" and "warehouse" databases.')


def init_neo4j():
    """Drop records in Neo4j."""
    # Truncate nodes
    neo4j = get_neo4j()
    neo4j.execute_query("MATCH (n) DETACH DELETE (n)")
    click.echo('Initialized neo4j database.')


@click.command('init-neo4j')
@with_appcontext
def init_neo4j_command():
    """Drop records in Neo4j."""
    init_neo4j()


def init_app(app):
    """Initialize app with the database commands."""
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_psql_command)
    app.cli.add_command(init_neo4j_command)
