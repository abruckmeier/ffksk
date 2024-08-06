select 
	*,
	allesUmsatz - dieb as bezahlt
from (
	select 
		"gekauftUm"::date as datum,
		sum(verkaufspreis) / 100.0 as allesUmsatz
	from (
		select 
			*
		from kiosk_gekauft a
		join profil_kioskuser b
		  on a.kaeufer_id = b.id
	) a, (
		select
		    stamp + interval '1 day' - interval '1 second' as stamp
		from (
			select
				"gekauftUm"::date as stamp
			from (
				select 
					*
				from kiosk_gekauft a
				join profil_kioskuser b
				  on a.kaeufer_id = b.id
			) uua
			where username = 'Dieb'
			group by "gekauftUm"::date
		) ua
	) b
	where "gekauftUm" <= stamp
	group by "gekauftUm"::date
) a
join (
	select 
		"gekauftUm"::date as datum,
		sum(verkaufspreis) / 100.0 as dieb
	from (
		select 
			*
		from (
			select 
				*
			from kiosk_gekauft a
			join profil_kioskuser b
			  on a.kaeufer_id = b.id
		) uuua
		where username='Dieb'
	) a, (
		select 
			stamp + interval '1 day' - interval '1 second' as stamp
		from (
			select
				"gekauftUm"::date as stamp
			from (
				select 
					*
				from kiosk_gekauft a
				join profil_kioskuser b
				  on a.kaeufer_id = b.id
			) uuuua
			where username = 'Dieb'
			group by "gekauftUm"::date
		) au
	) b
	where "gekauftUm" <= stamp
	group by "gekauftUm"::date
) b
	using(datum)
	
order by datum
