select
	b.produktpalette_id,
	b.name,
	b.anzahl,
	coalesce(s.anzahl,0) as stolen_anzahl,
	coalesce(s.anzahl*1.0 / (s.anzahl + b.anzahl) * 100 ,0) as spec_stolen_anzahl,
	b.ek + coalesce(s.ek,0) as ek,
	b.vk as vk,
	b.vk - (b.ek + coalesce(s.ek,0) ) as gewinn,
	(b.vk - (b.ek + coalesce(s.ek,0) ))/b.anzahl as spec_gewinn,
	coalesce(s.vk - s.ek,0) as entg_gewinn,
	coalesce((s.vk - s.ek),0) /b.anzahl as spec_entg_gewinn
from (
	select
		a.produktpalette_id,
		b."produktName" as name,
		count(*) as anzahl,
		sum(einkaufspreis)/100.0 as ek,
		sum(verkaufspreis)/100.0 as vk,
		sum(verkaufspreis)/100.0 - sum(einkaufspreis)/100.0 as gewinn
	from kiosk_gekauft a
	join kiosk_produktpalette b
	  on a.produktpalette_id = b.id
	join profil_kioskuser c
	  on a.kaeufer_id = c.id
	where c.username <> 'Dieb'
	group by b."produktName", a.produktpalette_id
) b
left join (
	select
		a.produktpalette_id,
		b."produktName" as name,
		count(*) as anzahl,
		sum(einkaufspreis)/100.0 as ek,
		sum(verkaufspreis)/100.0 as vk,
		sum(verkaufspreis)/100.0 - sum(einkaufspreis)/100.0 as gewinn
	from kiosk_gekauft a
	join kiosk_produktpalette b
	  on a.produktpalette_id = b.id
	join profil_kioskuser c
	  on a.kaeufer_id = c.id
	where c.username = 'Dieb'
	group by a.produktpalette_id, b."produktName"
) s
	using (produktpalette_id)
order by b.name