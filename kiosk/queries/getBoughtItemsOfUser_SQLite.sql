select
	a.kaeufer_id as kaeufer_id,
	b.id as produkt_id,
	b.produktName as produkt_name,
	count(*) as anzahl_gekauft
from kiosk_gekauft a
join kiosk_produktpalette b
	on a.produktpalette_id = b.id
where kaeufer_id = %s
group by b.produktName
