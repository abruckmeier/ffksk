select
	extract(month from a.month_start) as m,
	extract(year from a.month_start) as y,
	a.month_start as month_start,
	a.monthly_value as monthly_value
from (
	select
	  date_trunc('month', "gekauftUm")::date as month_start,
	  sum (verkaufspreis)/100.0 as monthly_value
	from kiosk_gekauft a
	join profil_kioskuser b
	  on a.kaeufer_id = b.id
	where b.username <> 'Dieb'
	group by month_start
	order by month_start
) a
where month_start > current_timestamp - interval '2 years'
