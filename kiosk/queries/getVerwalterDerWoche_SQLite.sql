select
	first_name,
	last_name,
	slackName,
	sum(anzahl) as items,
	count(*) as anlieferungen,
	sum(summeEingekauft) as eingekauft
from (
	select
	  first_name,
	  last_name,
	  slackName,
	  rounded_geliefert,
	  produktpalette_id,
	  sum(einkaufspreis)/100.0 as summeEingekauft,
	  count(einkaufspreis) as anzahl
	from (
		select
		  einkaufspreis,
		  verwalterEinpflegen_id,
		  strftime('%s', geliefertUm) - strftime('%s', geliefertUm) % 60 as rounded_geliefert,
		  geliefertUm,
		  produktpalette_id
		from kiosk_gekauft

		union all

		select
		  einkaufspreis,
		  verwalterEinpflegen_id,
		  strftime('%s', geliefertUm) - strftime('%s', geliefertUm) % 60 as rounded_geliefert,
		  geliefertUm,
		  produktpalette_id
		from kiosk_kiosk
		
	) a
	left join profil_kioskuser b
	 on (a.verwalterEinpflegen_id = b.id)
	where geliefertUm >= datetime(current_timestamp, '-7 days')
	group by verwalterEinpflegen_id, rounded_geliefert, produktpalette_id
)
group by first_name, last_name, slackName
order by anlieferungen desc
limit 3