set -e
sudo apt-get update
sudo apt-get install libpq-dev postgresql postgresql-contrib
pip3 install psycopg2
sudo su - postgres < ./init_postgre.sh
echo "Preparacion de PostgreSQL para el proyecto Bookalo terminada"