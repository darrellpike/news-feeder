from fabric import task

@task
def deploy(c):
    c.run('export DJANGO_SETTINGS_MODULE=adventure_agg.settings.production')
    # c.run('cd news-aggregator/ && . venv/bin/activate')
    # c.run('pip install -r requirements.txt')
    # c.run('./manage.py makemigrations --noinput')
    # c.run('./manage.py migrate --noinput')
    # c.run('./manage.py collectstatic --noinput')
    # c.run('sudo systemctl restart gunicorn celery')