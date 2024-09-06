#!/bin/bash
which gzip
which /bin/gzip
which pg_dump
which /bin/pg_dump
# Build the project
echo "Building the project..."
python3.12 -m pip install pipenv
python3.12 -m pipenv requirements > requirements.txt
python3.12 -m pip install -r requirements.txt

echo "Make Migration..."
python3.12 manage.py migrate --noinput

echo "Collect Static..."
python3.12 manage.py collectstatic --noinput --clear

echo "Setup groups and their permissions"
python3.12 manage.py shell -c "from scripts.initialisation import initGroupsAndPermissions as x; x.InitGroupsAndPermissions();"
python3.12 manage.py shell -c "from scripts.initialisation import initNecessaryUsers as x; x.initNecessaryUsers();"
