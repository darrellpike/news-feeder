FROM python:3.7

ENV PYTHONUNBUFFERED 1
ENV DJANGO_SETTINGS_MODULE=adventure_agg.settings.local

COPY . /srv/www/news-aggregator
WORKDIR /srv/www/news-aggregator
RUN pip install -r requirements.txt