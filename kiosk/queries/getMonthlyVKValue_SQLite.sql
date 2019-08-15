select
	strftime('%m', a.month_start) as week,
	strftime('%Y', a.month_start) as y,
	a.month_start as month_start,
	a.monthly_value as monthly_value
from (
	select
	  (date(date(gekauftUm), 'start of month')) month_start,
	  sum (verkaufspreis)/100.0 as monthly_value
	from kiosk_gekauft a
	join profil_kioskuser b
	  on a.kaeufer_id = b.id
	where b.username <> "Dieb"
	group by month_start
	order by month_start asc
) a
where month_start > datetime(datetime('now'), '-2 year')