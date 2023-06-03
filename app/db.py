import click
from flask import current_app, g
from flask.cli import with_appcontext
import psycopg


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
    pass


def close_db(e=None):
    """Close database connections if they exist."""
    psql_dbs = g.pop('psql', None)

    if psql_dbs is not None:
        for value in psql_dbs.values():
            value.close()


def import_sql(dbname: str, filepath: str):
    """Execute sql statements from given file."""
    psql = get_psql(dbname=dbname)

    with current_app.open_resource(filepath) as f:
        psql.execute(f.read().decode('utf8'))
        psql.commit()


@click.command('init-db')
@with_appcontext
def init_db_command():
    """Create tables."""
    import_sql('database/create_tables_psqlvsneo4j.sql')
    import_sql('warehouse', 'database/create_tables_warehouse.sql')
    import_sql('testdata', 'database/create_tables_testdata.sql')
    click.echo('Initialized the database.')


def init_app(app):
    """Initialize app with the database commands."""
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
