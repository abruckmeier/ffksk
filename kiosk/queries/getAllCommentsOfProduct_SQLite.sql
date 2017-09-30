select
	produktpalette_id,
	b.produktName as produkt_name,
	erstellt,
	kommentar
from kiosk_produktkommentar a
join kiosk_produktpalette b
	on a.produktpalette_id = b.id
where produktpalette_id = %s
order by erstellt desc