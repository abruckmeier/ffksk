select 
	'alle' as what,
	sum(verkaufspreis) / 100.0 as preis
from (
	select 
		*
	from kiosk_gekauft a
	join profil_kioskuser b
	  on a.kaeufer_id = b.id
	where gekauftUm <= %s
)

union all

select
	'Dieb' as what,
	sum(verkaufspreis) / 100.0 as preis
from (
	select 
		*
	from kiosk_gekauft a
	join profil_kioskuser b
	  on a.kaeufer_id = b.id
	where gekauftUm <= %s
)
where username = 'Dieb'

union all

select
	'bezahlt' as what,
	sum(verkaufspreis) / 100.0 as preis
from (
	select 
		*
	from kiosk_gekauft a
	join profil_kioskuser b
	  on a.kaeufer_id = b.id
	where gekauftUm <= %s
)
where username <> 'Dieb'