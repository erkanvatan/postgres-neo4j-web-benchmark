import psycopg

import click
from flask import current_app, g
from flask.cli import with_appcontext


def get_psql():
    """Connect to PostgreSQL database and return cursor of connection."""

    CONN_PARAMETERS = {"host": current_app.config["PSQL_HOST"], "dbname": current_app.config["PSQL_DB_NAME"],
                       "user": current_app.config["PSQL_DB_USER"], "password": current_app.config["PSQL_DB_PASSWORD"],
                       "port": current_app.config["PSQL_PORT"]}
    if 'psql' not in g:
        # `g` object is used to store connection for multiple access to a data
        # during a request
        g.psql = psycopg.connect(**CONN_PARAMETERS)

    return g.psql


def get_neo4j():
    """Connect to Neo4j graph database and return connection."""
    pass


def close_db(e=None):
    """Close database connections if they exist."""
    psql = g.pop('psql', None)

    if psql is not None:
        psql.close()


def import_sql(filepath):
    """Execute sql statements from the file."""
    psql = get_psql()

    with current_app.open_resource(filepath) as f:
        psql.execute(f.read().decode('utf8'))


@click.command('init-db')
@with_appcontext
def init_db_command():
    """Clear the existing data and create new tables."""
    import_sql('database/schema.sql')
    click.echo('Initialized the database.')


def init_app(app):
    """Initialize app with the database commands."""
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
