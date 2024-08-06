#!/bin/bash

# Build the project
echo "Building the project..."
python3.12 -m pip install pipenv
python3.12 -m pipenv requirements > requirements.txt
python3.12 -m pip install -r requirements.txt

echo "Make Migration..."
python3.12 manage.py migrate --noinput

echo "Collect Static..."
python3.12 manage.py collectstatic --noinput --clear
