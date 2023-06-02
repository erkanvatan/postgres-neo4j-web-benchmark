# Makefile for postgres-neo4j-python-benchmark
#
# @author arensonzz

# Source default environment variables from .env file
include .env

.DELETE_ON_ERROR:

# Default target
all: clean up run

#
# General Targets
#
up:
	# Start PostgreSQL and Neo4j nodes.
	docker compose up -d


run: .env
	# Start Werkzeug Flask server
	HTTPS_MODE=${HTTPS_MODE} python3 app.py


sass:
	# Continuously compile SASS files into CSS files
	sass --watch ./app/sass:./app/static/styles --style expanded --no-source-map


clean:
	# Stop PostgreSQL and Neo4j nodes.
	docker compose down --volumes

	# Clear stored Flask sessions.
	rm -rf ./flask_session

	# Clear Python cache files.
	rm -rf ./app/__pycache__

#
# Private Targets
#

# Create .env file from .env.example if it does not exist
.env:
	cp .env.example .env


.PHONY: all up run sass clean
