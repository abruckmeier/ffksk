#!/bin/bash

# Build the project
echo "Building the project..."
uvx pipenv install --deploy --ignore-pipfile
uvx pipenv requirements > requirements.txt

echo "Make Migration..."
uvx pipenv run python manage.py migrate --noinput

echo "Collect Static..."
uvx pipenv run python manage.py collectstatic --noinput --clear

echo "Setup groups and their permissions"
uvx pipenv run python manage.py shell -c "from scripts.initialisation import initGroupsAndPermissions as x; x.InitGroupsAndPermissions();"
uvx pipenv run python manage.py shell -c "from scripts.initialisation import initNecessaryUsers as x; x.initNecessaryUsers();"
