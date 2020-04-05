.PHONY: build-container load-data install-python-dependencies run

build-container: docker/Dockerfile sql/setup.sql
	docker build -f docker/Dockerfile -t covid19griddb sql

run: build-container
	docker run --rm --name timescaledb -p 5434:5432 covid19griddb

install-python-dependencies:
	python3 -m venv .env && . .env/bin/activate &&\
	pip install -r requirements.txt

alameda-county-parcel-address.tar.gz:
	wget http://files.gtf.fyi/alameda-county-parcel-address.tar.gz

data/alameda-address.csv:
	tar -xzvf alameda-county-parcel-address.tar.gz

data/alameda-parcels.geojson:
	tar -xzvf alameda-county-parcel-address.tar.gz

load-data: data/alameda-address.csv data/alameda-parcels.geojson
	. .env/bin/activate &&\
	python scripts/load_alameda_geo.py &&\
	python scripts/load_alameda_address.py
