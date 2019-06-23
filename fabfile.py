#!/usr/bin/env python3

from fabric.api import hide, env, settings, abort, run, cd, shell_env
from fabric.colors import magenta, red
from fabric.contrib.files import append
from fabric.contrib.project import rsync_project
import os

env.user = 'root'
env.abort_on_prompts = True
PATH = '/home/viceroy627/news-aggregator'
ENV_FILE = '/etc/profile.d/variables.sh'
VARIABLES = ('SECRET_KEY', )

def deploy():
    def rsync():
        exclusions = ('.git*', '.env', '*.sock*', '*.lock', '*.pyc', '*cache*',
                      '*.log',  'log/', 'id_rsa*', 'maintenance')
        rsync_project(PATH, './', exclude=exclusions, delete=True)

    def docker_compose(command):
        with cd(PATH):
            with shell_env(CI_BUILD_REF_NAME=os.getenv(
                    'CI_BUILD_REF_NAME', 'master')):
                run('set -o pipefail; docker-compose %s | tee' % command)

    variables_set = True
    for var in VARIABLES + ('CI_BUILD_TOKEN', ):
        if os.getenv(var) is None:
            variables_set = False
            print(red('ERROR: environment variable ' + var + ' is not set.'))
    if not variables_set:
        abort('Missing required parameters')
    with hide('commands'):
        run('rm -f "%s"' % ENV_FILE)
        append(ENV_FILE,
               ['export %s="%s"' % (var, val) for var, val in zip(
                   VARIABLES, map(os.getenv, VARIABLES))])

    run('docker login -u %s -p %s %s' % (os.getenv('REGISTRY_USER',
                                                   'gitlab-ci-token'),
                                         os.getenv('CI_BUILD_TOKEN'),
                                         os.getenv('CI_REGISTRY',
                                                   'registry.gitlab.com')))

    with settings(warn_only=True):
        with hide('warnings'):
            need_bootstrap = run('docker ps | grep -q web').return_code != 0
    if need_bootstrap:
        print(magenta('No previous installation found, bootstrapping'))
        rsync()
        docker_compose('up -d')

    run('touch %s/nginx/maintenance && docker kill -s HUP nginx_1' % PATH)
    rsync()
    docker_compose('pull')
    docker_compose('up -d')
    run('rm -f %s/nginx/maintenance && docker kill -s HUP nginx_1' % PATH)