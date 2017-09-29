select
	a.produktpalette_id,
	b.produktName as name,
	count(*) as anzahl,
	sum(einkaufspreis)/100.0 as ek,
	sum(verkaufspreis)/100.0 as vk,
	sum(verkaufspreis)/100.0 - sum(einkaufspreis)/100.0 as gewinn
from kiosk_gekauft a
join kiosk_produktpalette b
  on a.produktpalette_id = b.id
join profil_kioskuser c
  on a.kaeufer_id = c.id
where c.username <> "Dieb"
group by produktpalette_id
order by gewinn desc