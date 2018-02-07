select
	strftime('%m', a.month_start) as month,
	strftime('%Y', a.month_start) as y,
	a.month_start as month_start,
	a.monthly_value as monthly_value
from (
	select
	  (date(date('now'), 'start of month')) as month_start,
	  sum (verkaufspreis)/100.0 as monthly_value
	from kiosk_gekauft a
	join profil_kioskuser b
	  on a.kaeufer_id = b.id
	where b.username <> "Dieb"
	  and date(a.gekauftUm) >= month_start
	group by month_start
	order by month_start asc
) a
