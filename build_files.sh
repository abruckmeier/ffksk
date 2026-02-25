#!/bin/bash

# Build the project
echo "Building the project..."
uv pip install pipenv
uv run python -m pipenv requirements > requirements.txt
uv pip install -r requirements.txt

echo "Make Migration..."
uv run python manage.py migrate --noinput

echo "Collect Static..."
uv run python manage.py collectstatic --noinput --clear

echo "Setup groups and their permissions"
uv run python manage.py shell -c "from scripts.initialisation import initGroupsAndPermissions as x; x.InitGroupsAndPermissions();"
uv run python manage.py shell -c "from scripts.initialisation import initNecessaryUsers as x; x.initNecessaryUsers();"
