select
	a.day_start as day_start,
	a.dayly_value as dayly_value
from (
	select
	  current_date as day_start,
	  sum (verkaufspreis)/100.0 as dayly_value
	from kiosk_gekauft a
	join profil_kioskuser b
	  on a.kaeufer_id = b.id
	where b.username <> 'Dieb'
	  and a."gekauftUm"::date >= current_date
	group by day_start
	order by day_start
) a
