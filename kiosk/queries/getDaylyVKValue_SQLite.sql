select
	datum,
	dayly_value,
	(select 
		sum(b.dayly_value) 
	from (
		select
		  "gekauftUm"::date as datum,
		  sum (verkaufspreis)/100.0 as dayly_value
		from kiosk_gekauft a
		join profil_kioskuser b
		  on a.kaeufer_id = b.id
		where b.username <> 'Dieb'
		group by "gekauftUm"::date
		order by "gekauftUm"::date
	) b where b.datum <= a.datum) as accumulated_value
from (
	select
	  "gekauftUm"::date as datum,
	  sum (verkaufspreis)/100.0 as dayly_value
	from kiosk_gekauft a
	join profil_kioskuser b
	  on a.kaeufer_id = b.id
	where b.username <> 'Dieb'
	group by "gekauftUm"::date
	order by "gekauftUm"::date
) a
where datum > current_timestamp - interval '2 months'
