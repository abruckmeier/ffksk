select
	a.day_start as day_start,
	a.dayly_value as dayly_value
from (
	select
	  date('now') as day_start,
	  sum (verkaufspreis)/100.0 as dayly_value
	from kiosk_gekauft a
	join profil_kioskuser b
	  on a.kaeufer_id = b.id
	where b.username <> "Dieb"
	  and date(a.gekauftUm) >= day_start
	group by day_start
	order by day_start asc
) a