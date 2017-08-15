from django.conf import settings
from django.db import connection


def readFromDatabase(fileToQuery, queryArgumentList=[]):
	dbInUse = getattr(settings,'DB_IN_USE') # 'Postgre','SQLite'
	BASE_DIR = getattr(settings,'BASE_DIR')

	fileName = BASE_DIR + "/kiosk/queries/" + fileToQuery + "_" + dbInUse + ".sql"
	# Hier sollte dann auf dem Server der absolute Pfad stehen. Siehe OneNote

	with open(fileName,"r") as file:
		query = file.read()

	cur = connection.cursor()
	cur.execute(query,queryArgumentList)
	columns = [col[0] for col in cur.description]
	items = [dict(zip(columns,row)) for row in cur.fetchall()]

	return(items)
