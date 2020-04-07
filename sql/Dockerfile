FROM ubuntu:19.10

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
   curl \
   gnupg \
   software-properties-common

RUN echo "deb http://apt.postgresql.org/pub/repos/apt/ $(lsb_release -c -s)-pgdg main" | tee /etc/apt/sources.list.d/pgdg.list
RUN curl https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -
RUN add-apt-repository ppa:timescale/timescaledb-ppa

RUN apt-get update && apt-get install -y \
   postgresql-11 \
   timescaledb-postgresql-11 \
   postgresql-11-postgis-3 \
   postgresql-plpython3-11 \
   python3-dev \
   python3-pip

RUN python3 -m pip install openlocationcode

RUN timescaledb-tune --quiet --yes
RUN echo "host all  all    0.0.0.0/0  password" >> /etc/postgresql/11/main/pg_hba.conf
RUN echo "listen_addresses='*'" >> /etc/postgresql/11/main/postgresql.conf

ADD setup.sql /opt/setup.sql

USER postgres
RUN /etc/init.d/postgresql start &&\
    psql --command "CREATE USER covid19 WITH SUPERUSER PASSWORD 'covid19databasepassword';" &&\
    createdb -O covid19 covid19 &&\
    psql -d covid19 --command "CREATE EXTENSION postgis;" &&\
    psql -d covid19 --command "CREATE EXTENSION plpython3u;" &&\
    psql -d covid19 --command "CREATE EXTENSION timescaledb CASCADE;" &&\
    psql -d covid19 --command "\i opt/setup.sql"
RUN pg_lsclusters

# Expose the PostgreSQL port
EXPOSE 5432

CMD ["/usr/lib/postgresql/11/bin/postgres", "-D", "/var/lib/postgresql/11/main", "-c", "config_file=/etc/postgresql/11/main/postgresql.conf"]
