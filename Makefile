# Makefile for postgres-neo4j-python-benchmark
#
# @author arensonzz

# Source default environment variables from .env file
include .env

.DELETE_ON_ERROR:

# Default target
all: clean generate-data run

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


clean: _mvn-clean
	# Stop PostgreSQL and Neo4j nodes.
	docker compose down --volumes

	# Clear stored Flask sessions.
	rm -rf ./flask_session

	# Clear Python cache files.
	rm -rf ./app/__pycache__

	# Clear the "data" directory.
	# @docker run -it -v "$(shell pwd)/data":/usr/src/tmp/jars alpine find /usr/src/tmp/jars -mindepth 1 -delete || exit 0

	# Clear the ".neo4j" directory
	# @docker run -it -v "$(shell pwd)/.neo4j":/usr/src/tmp/.neo4 alpine find /usr/src/tmp/.neo4j -delete || exit 0


#
# Data Generators
#
data-generator-warehouse: up _mvn-package _mvn-clean
	# Create output folder
	mkdir -p data/warehouse

	# Start "warehouse" data generator.
	@docker run -it --network="${PROJECT_NAME}_default" --env-file=".env" -v "$(shell pwd)/data":/usr/src/mymaven -w /usr/src/mymaven eclipse-temurin:8-jre-alpine java -jar warehouse_data_generator-1.0-SNAPSHOT.jar

	# Copy CSV files into Neo4j "import" folder.
	@docker cp data/warehouse/ ${PROJECT_NAME}-neo4j-1:/var/lib/neo4j/import/


data-generator-university:
	# Create output folder
	mkdir -p data/university

	# Start "university" data generator.
	python3 data_generators/university.py

	# Copy CSV files into Neo4j "import" folder.
	@docker cp data/university/ ${PROJECT_NAME}-neo4j-1:/var/lib/neo4j/import/


#
# Private Targets
#

# Create .env file from .env.example if it does not exist
.env:
	cp .env.example .env

_mvn-package:
	# Compile the project using "mvn" and package it in a JAR file.
	@docker run -it -v "$(shell pwd)/data_generators/warehouse":/usr/src/mymaven -v ${PROJECT_NAME}-maven-repo:/root/.m2 -w /usr/src/mymaven maven:3.3-jdk-8 mvn clean package
	mkdir -p data
	cp data_generators/warehouse/target/warehouse_data_generator-1.0-SNAPSHOT.jar data


_mvn-clean:
	# Clear the "target" directory.
	@docker run -it -v "$(shell pwd)/data_generators/warehouse":/usr/src/tmp alpine find /usr/src/tmp/target /usr/src/tmp/dependency-reduced-pom.xml -delete || exit 0

.PHONY: all up run sass clean data-generator-warehouse data-generator-university _mvn-package _mvn-clean
