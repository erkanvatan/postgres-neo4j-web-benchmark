import os

TEMPLATES_AUTO_RELOAD = True
SECRET_KEY = os.environ.get("SECRET_KEY", "dev")

# PostgreSQL database config
PSQL_HOST = os.environ.get("POSTGRES_HOST", "localhost")
PSQL_PORT = os.environ.get("PSQL_PORT", "5432")
PSQL_DB_NAME = os.environ.get("POSTGRES_DB", "psqlvsneo4j")
PSQL_DB_USER = os.environ.get("POSTGRES_USER", "postgres")
PSQL_DB_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "postgres")

# Neo4j database config, NEO4J_AUTH has the form "user/password"
NEO4J_HOST = os.environ.get("NEO4J_HOST", "localhost")
NEO4J_PORT = os.environ.get("NEO4J_PORT", "7687")
NEO4J_DB_USER, NEO4J_DB_PASSWORD = os.environ.get("NEO4J_AUTH", "neo4j/12345678").split("/", 1)
