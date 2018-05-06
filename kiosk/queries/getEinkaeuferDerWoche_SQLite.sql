select
	first_name,
	last_name,
	slackName,
	summeEingekauft,
	summe_umsatz,
	anzahl,
	summe_umsatz/1.0 + summeEingekauft/10.0 + anzahl/100.0 as ranking
from (
	select
	  first_name,
	  last_name,
	  slackName,
	  sum(einkaufspreis)/100.0 as summeEingekauft,
	  sum(verkaufspreis-einkaufspreis)/100.0 as summe_umsatz,
	  count(einkaufspreis) as anzahl
	from (
		select
		  einkaufspreis,
		  verkaufspreis,
		  einkaeufer_id,
		  geliefertUm
		from kiosk_gekauft

		union all

		select
		  a.einkaufspreis,
		  b.verkaufspreis,
		  a.einkaeufer_id,
		  a.geliefertUm
		from kiosk_kiosk a
		left join (
			select
				a.produktpalette_id,
				a.verkaufspreis
			from kiosk_produktverkaufspreise a
			join (
				select
				  a.produktpalette_id,
				  max(a."gueltigAb") as "gueltigAb"
				from
				  kiosk_produktverkaufspreise a
				where
				  a."gueltigAb" < current_timestamp
				group by
				  a.produktpalette_id
			  ) b
			  using (produktpalette_id,"gueltigAb")
			) b
				using(produktpalette_id)
		
	) a
	left join profil_kioskuser b
	 on (a.einkaeufer_id = b.id)
	where geliefertUm >= datetime(current_timestamp, '-7 days')
	group by einkaeufer_id
)
where anzahl > 0
order by ranking desc
limit 3