#!/bin/bash

eval "$(ssh-agent -s)" 
chmod 600 .travis/bookalo_key 
ssh-add .travis/bookalo_key 

ssh roberta@bookalo.es "sudo systemctl stop uwsgi"

git config --global push.default matching
git remote add deploy ssh://git@$IP$DEPLOY_DIR
git push deploy master

ssh roberta@bookalo.es "source bin/activate && pip install -r src/requirements.txt && deactivate"
ssh roberta@bookalo.es "source bin/activate && python src/manage.py collectstatic --noinput && python src/manage.py makemigrations && python src/manage.py migrate --run-syncdb && deactivate"
ssh roberta@bookalo.es "sudo systemctl start uwsgi"
