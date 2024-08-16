select
	extract(week from a.week_start) as week,
	extract(year from a.week_start) as y,
	a.week_start as week_start,
	a.weekly_value as weekly_value
from (
	select
	  date_trunc('week', current_date) - interval '7 days' as week_start,
	  sum (verkaufspreis)/100.0 as weekly_value
	from kiosk_gekauft a
	join profil_kioskuser b
	  on a.kaeufer_id = b.id
	where b.username <> 'Dieb'
	  and a."gekauftUm" <= date_trunc('week', current_date) - interval '7 days'
	group by week_start
	order by week_start
) a
