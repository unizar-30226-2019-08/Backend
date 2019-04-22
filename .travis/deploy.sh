#!/bin/bash

eval "$(ssh-agent -s)" # Start ssh-agent cache
chmod 600 .travis/bookalo_key # Allow read access to the private key
ssh-add .travis/bookalo_key # Add the private key to SSH

git config --global push.default matching
git remote add deploy ssh://git@$IP$DEPLOY_DIR
git push deploy master

# Skip this command if you don't need to execute any additional commands after deploying.
ssh roberta@$IP <<EOF
  cd $DEPLOY_DIR
  touch test_fue_bien
EOF
