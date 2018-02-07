select
	a.day_start as day_start,
	a.dayly_value as dayly_value
from (
	select
	  date(date('now'),'-1 day') as day_start,
	  date('now') as day_end,
	  sum (verkaufspreis)/100.0 as dayly_value
	from kiosk_gekauft a
	join profil_kioskuser b
	  on a.kaeufer_id = b.id
	where b.username <> "Dieb"
	  and date(a.gekauftUm) >= day_start
	  and date(a.gekauftUm) < day_end
	group by day_start
	order by day_start asc
) a
