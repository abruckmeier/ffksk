pipenv requirements > requirements.txt
pip install -r requirements.txt
python3.12 manage.py migrate
python3.12 manage.py collectstatic
