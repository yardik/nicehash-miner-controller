FROM python:3.9.4-slim-buster
ENV PYTHONUNBUFFERED True
ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . ./
RUN pip install Flask gunicorn requests
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app