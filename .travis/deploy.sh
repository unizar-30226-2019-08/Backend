#!/bin/bash

eval "$(ssh-agent -s)" # Start ssh-agent cache
chmod 600 .travis/bookalo_key # Allow read access to the private key
ssh-add .travis/bookalo_key # Add the private key to SSH

ssh roberta@bookalo.es "sudo systemctl stop uwsgi"

git config --global push.default matching
git remote add deploy ssh://git@$IP$DEPLOY_DIR
git push deploy master

ssh roberta@bookalo.es "source bin/activate && python src/manage.py collectstatic --noinput && python src/manage.py makemigrations && python src/manage.py migrate --syn-db && deactivate"
ssh roberta@bookalo.es "sudo systemctl start uwsgi"
