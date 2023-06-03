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


clean: _mvn-clean
	# Stop PostgreSQL and Neo4j nodes.
	docker compose down --volumes

	# Clear stored Flask sessions.
	rm -rf ./flask_session

	# Clear Python cache files.
	rm -rf ./app/__pycache__

	# Clear the "jars" directory.
	@docker run -it -v "$(shell pwd)/jars":/usr/src/tmp/jars alpine find /usr/src/tmp/jars -mindepth 1 -delete || exit 0

# 
# Data Generator
#
generate-data: _mvn-package _mvn-clean
	# Start Java data generator.
	@docker run -it --network="${PROJECT_NAME}_default" --env-file=".env" -v "$(shell pwd)/jars":/usr/src/mymaven -w /usr/src/mymaven eclipse-temurin:8-jre-alpine java -jar data_generator-1.0-SNAPSHOT.jar


#
# Private Targets
#

# Create .env file from .env.example if it does not exist
.env:
	cp .env.example .env

_mvn-package:
	# Compile the project using "mvn" and package it in a JAR file.
	@docker run -it -v "$(shell pwd)/data_generator":/usr/src/mymaven -v ${PROJECT_NAME}-maven-repo:/root/.m2 -w /usr/src/mymaven maven:3.3-jdk-8 mvn clean package
	mkdir -p jars
	cp data_generator/target/data_generator-1.0-SNAPSHOT.jar jars


_mvn-clean:
	# Clear the "target" directory.
	@docker run -it -v "$(shell pwd)/data_generator":/usr/src/tmp alpine find /usr/src/tmp/target /usr/src/tmp/dependency-reduced-pom.xml -delete || exit 0

.PHONY: all up run sass clean generate-data _mvn-package _mvn-clean
