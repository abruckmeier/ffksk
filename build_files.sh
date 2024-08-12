#!/bin/bash
apt-get update -y
apt-get install -y locales dos2unix
sed -i -e 's/# de_DE.UTF-8 UTF-8/de_DE.UTF-8 UTF-8/' /etc/locale.gen
dpkg-reconfigure --frontend=noninteractive locales
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
