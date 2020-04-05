.PHONY: build-container

build-container: docker/Dockerfile sql/setup.sql
	docker build -f docker/Dockerfile -t covid19griddb sql

run: build-container
	docker run --rm --name timescaledb -p 5434:5432 covid19griddb
