select
  *,
  a.cnt_kiosk + a.cnt_persEKL + a.cnt_ek_vormerk as summe
from
(
	select
	  a.id,
	  a.maxKapazitaet,
	  a.schwelleMeldung,
	  a.paketgroesseInListe,
	  case
		when a.cnt_kiosk is NULL then 0
		else a.cnt_kiosk
	  end as cnt_kiosk,
	  case
		when a.cnt_persEKL is NULL then 0
		else a.cnt_persEKL
	  end as cnt_persEKL,
	  case
		when a.cnt_ek_vormerk is NULL then 0
		else a.cnt_ek_vormerk
	  end as cnt_ek_vormerk
	from
	(
		select
		  a.id,
		  aa.maxKapazitaet,
		  aa.schwelleMeldung,
		  aa.paketgroesseInListe,
		  a.produktName,
		  b.cnt_kiosk,
		  c.cnt_persEKL,
		  d.cnt_ek_vormerk
		from kiosk_produktpalette a
		left join kiosk_kioskkapazitaet aa
		  on a.id = aa.produktpalette_id
		left join 
		(
			select
			  produktpalette_id,
			  count(*) as cnt_kiosk
			from kiosk_kiosk
			group by produktpalette_id
		) b
		  on a.id = b.produktpalette_id
		left join 
		(
			select
			  produktpalette_id,
			  count(*) as cnt_persEKL
			from kiosk_zumeinkaufvorgemerkt
			group by produktpalette_id
		) c
		  on a.id = c.produktpalette_id
		left join 
		(
			select
			  produktpalette_id,
			  count(*) as cnt_ek_vormerk
			from kiosk_einkaufsliste
			group by produktpalette_id
		) d
		  on a.id = d.produktpalette_id
		where a.imVerkauf is 1
	) a
) a
