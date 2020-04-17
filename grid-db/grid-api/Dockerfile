FROM python:3.8-slim-buster

ENV FLASK_APP /opt/app.py
ENV FLASK_RUN_HOST 0.0.0.0

ADD requirements.txt /opt/requirements.txt
RUN pip install -r /opt/requirements.txt

ADD app.py /opt/app.py

CMD ["flask", "run", "--with-threads"]
