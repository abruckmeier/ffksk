with database as (
	select 
		*
	from kiosk_gekauft a
	join profil_kioskuser b
	  on a.kaeufer_id = b.id
	where gekauftUm <= %s
)

select 
	'alle' as what,
	sum(verkaufspreis) / 100.0 as preis
from database

union all

select
	'Dieb' as what,
	sum(verkaufspreis) / 100.0 as preis
from database
where username = 'Dieb'

union all

select
	'bezahlt' as what,
	sum(verkaufspreis) / 100.0 as preis
from database
where username <> 'Dieb'