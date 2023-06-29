FROM python:3.7-slim-buster

WORKDIR /app

COPY . .
RUN apt-get update && apt-get install -y --no-install-recommends python3-dev default-libmysqlclient-dev build-essential 
RUN pip install -r requirements.txt

ENV FLASK_APP="jiken"

EXPOSE 4999

# Bind to both IPv4 and IPv6
ENV GUNICORN_CMD_ARGS="--bind=[::]:4999 --workers=1"

# replace APP_NAME with module name
CMD ["gunicorn", "jiken:app"]