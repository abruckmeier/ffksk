with database as (
	select 
		*
	from kiosk_gekauft a
	join profil_kioskuser b
	  on a.kaeufer_id = b.id
),
databaseDieb as (
	select 
		*
	from database
	where username='Dieb'
),
timestamps_1 as (
	select
		date(gekauftUm) as stamp
	from database
	where username = 'Dieb'
	group by stamp
),
timestamps as (
	select 
		datetime(stamp,'+1 day','-1 second') as stamp
	from timestamps_1
)

select 
	*,
	allesUmsatz - dieb as bezahlt
from (
	select 
		date(stamp) as datum,
		sum(verkaufspreis) / 100.0 as allesUmsatz
	from database a, timestamps b
	where gekauftUm <= stamp
	group by stamp
) a
join (
	select 
		date(stamp) as datum,
		sum(verkaufspreis) / 100.0 as dieb
	from databaseDieb a, timestamps b
	where gekauftUm <= stamp
	group by stamp
) b
	using(datum)
	
order by datum asc