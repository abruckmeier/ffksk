select
	datum,
	dayly_value,
	(select 
		sum(b.dayly_value) 
	from (
		select
		  date(gekauftUm) as datum,
		  sum (verkaufspreis)/100.0 as dayly_value
		from kiosk_gekauft
		group by datum
		order by gekauftUm asc
	) b where b.datum <= a.datum) as accumulated_value
from (
	select
	  date(gekauftUm) as datum,
	  sum (verkaufspreis)/100.0 as dayly_value
	from kiosk_gekauft
	group by datum
	order by gekauftUm asc
) a
