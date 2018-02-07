select
	strftime('%W', a.week_start) as week,
	strftime('%Y', a.week_start) as y,
	a.week_start as week_start,
	a.weekly_value as weekly_value
from (
	select
	  (date(date('now'), 'weekday 0', '-7 day')) as week_start,
	  sum (verkaufspreis)/100.0 as weekly_value
	from kiosk_gekauft a
	join profil_kioskuser b
	  on a.kaeufer_id = b.id
	where b.username <> "Dieb"
	  and date(a.gekauftUm) >= week_start
	group by week_start
	order by week_start asc
) a