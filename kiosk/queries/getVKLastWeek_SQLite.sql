select
	strftime('%W', a.week_start) as week,
	strftime('%Y', a.week_start) as y,
	a.week_start as week_start,
	a.weekly_value as weekly_value
from (
	select
	  (date(date('now'), 'weekday 0', '-14 day')) as week_start,
	  (date(date('now'), 'weekday 0', '-8 day')) as week_end,
	  sum (verkaufspreis)/100.0 as weekly_value
	from kiosk_gekauft a
	join profil_kioskuser b
	  on a.kaeufer_id = b.id
	where b.username <> "Dieb"
	  and date(a.gekauftUm) >= week_start
	  and date(a.gekauftUm) <= week_end
	group by week_start
	order by week_start asc
) a
