select
	produktpalette_id,
	b.produktName as produkt_name,
	erstellt,
	kommentar
from kiosk_produktkommentar a
join (
	select
	  produktpalette_id,
	  max(erstellt) as erstellt
	from kiosk_produktkommentar
	where erstellt < current_timestamp
	group by produktpalette_id  
)
	using(produktpalette_id,erstellt)
join kiosk_produktpalette b
	on a.produktpalette_id = b.id

order by produkt_name asc