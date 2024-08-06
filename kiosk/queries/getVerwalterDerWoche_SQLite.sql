select
	first_name,
	last_name,
	"slackName",
	sum(anzahl) as items,
	count(*) as anlieferungen,
	sum(summeEingekauft) as eingekauft
from (
	select
	  first_name,
	  last_name,
	  "slackName",
	  rounded_geliefert,
	  produktpalette_id,
	  sum(einkaufspreis)/100.0 as summeEingekauft,
	  count(einkaufspreis) as anzahl
	from (
		select
		  einkaufspreis,
		  "verwalterEinpflegen_id",
		  extract(epoch from "geliefertUm") - extract(epoch from "geliefertUm") %% 60 as rounded_geliefert,
		  "geliefertUm",
		  produktpalette_id
		from kiosk_gekauft

		union all

		select
		  einkaufspreis,
		  "verwalterEinpflegen_id",
		  extract(epoch from "geliefertUm") - extract(epoch from "geliefertUm") %% 60 as rounded_geliefert,
		  "geliefertUm",
		  produktpalette_id
		from kiosk_kiosk
		
	) a
	left join profil_kioskuser b
	 on (a."verwalterEinpflegen_id" = b.id)
	where "geliefertUm" >= current_timestamp - interval '7 days'
	group by "verwalterEinpflegen_id", rounded_geliefert, produktpalette_id, first_name, last_name, "slackName"
) ua
group by first_name, last_name, "slackName"
order by anlieferungen desc
limit 3
