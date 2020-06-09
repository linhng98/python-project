FROM python:3-alpine
COPY ./source /usr/src/flask-webapp
WORKDIR /usr/src/flask-webapp
RUN pip install flask flask-failsafe
CMD ["python", "hello-flask.py"]