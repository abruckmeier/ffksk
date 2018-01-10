select 
	*,
	allesUmsatz - dieb as bezahlt
from (
	select 
		date(stamp) as datum,
		sum(verkaufspreis) / 100.0 as allesUmsatz
	from (
		select 
			*
		from kiosk_gekauft a
		join profil_kioskuser b
		  on a.kaeufer_id = b.id
	) a, (
		select 
			datetime(stamp,'+1 day','-1 second') as stamp
		from (
			select
				date(gekauftUm) as stamp
			from (
				select 
					*
				from kiosk_gekauft a
				join profil_kioskuser b
				  on a.kaeufer_id = b.id
			)
			where username = 'Dieb'
			group by stamp
		)
	) b
	where gekauftUm <= stamp
	group by stamp
) a
join (
	select 
		date(stamp) as datum,
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
		)
		where username='Dieb'
	) a, (
		select 
			datetime(stamp,'+1 day','-1 second') as stamp
		from (
			select
				date(gekauftUm) as stamp
			from (
				select 
					*
				from kiosk_gekauft a
				join profil_kioskuser b
				  on a.kaeufer_id = b.id
			)
			where username = 'Dieb'
			group by stamp
		)
	) b
	where gekauftUm <= stamp
	group by stamp
) b
	using(datum)
	
order by datum asc