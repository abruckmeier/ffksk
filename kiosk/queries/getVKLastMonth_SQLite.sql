select
	extract(month from a.month_start) as month,
	extract(year from a.month_start) as y,
	a.month_start as month_start,
	a.monthly_value as monthly_value
from (
	select
	  date_trunc('month', current_date)::date as month_end,
	  date_trunc('month', current_date)::date - interval '1 month' as month_start,
	  sum (verkaufspreis)/100.0 as monthly_value
	from kiosk_gekauft a
	join profil_kioskuser b
	  on a.kaeufer_id = b.id
	where b.username <> 'Dieb'
	  and a."gekauftUm"::date >= date_trunc('month', current_date)::date - interval '1 month'
	  and a."gekauftUm"::date <= date_trunc('month', current_date)::date
	group by month_start
	order by month_start
) a
