createdb bookalo
createuser bookalo_admin
psql <<EOF
ALTER USER bookalo_admin WITH PASSWORD 'bookalomaster';
GRANT ALL PRIVILEGES ON DATABASE bookalo TO bookalo_admin;
\q
EOF
exit