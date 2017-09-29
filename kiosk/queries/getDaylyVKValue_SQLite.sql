with a as (
	select
	  date(gekauftUm) as datum,
	  sum (verkaufspreis)/100.0 as dayly_value
	from kiosk_gekauft
	group by datum
	order by gekauftUm asc
)
select
	datum,
	dayly_value,
	(select sum(b.dayly_value) from a b where b.datum <= a.datum) as accumulated_value
from a
