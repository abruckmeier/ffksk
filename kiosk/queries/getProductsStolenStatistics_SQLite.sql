select
	a.produktpalette_id,
	b.produktName as name,
	count(a.produktpalette_id) as all_anzahl,
	sum(a.verkaufspreis) as all_vk,
	d.anzahl as stolen_anzahl,
	d.vk/100.0 as stolen_vk,
	d.vk* 100.0 / sum(a.verkaufspreis)  as rel_stolen
from kiosk_gekauft a
join kiosk_produktpalette b
  on a.produktpalette_id = b.id
join profil_kioskuser c
  on a.kaeufer_id = c.id
join (
	select
		a.produktpalette_id,
		b.produktName as name,
		count(*) as anzahl,
		sum(verkaufspreis) as vk
	from kiosk_gekauft a
	join kiosk_produktpalette b
	  on a.produktpalette_id = b.id
	join profil_kioskuser c
	  on a.kaeufer_id = c.id
	where c.username = "Dieb"
	group by a.produktpalette_id
) d
	using(produktpalette_id)
group by a.produktpalette_id
order by stolen_vk desc
