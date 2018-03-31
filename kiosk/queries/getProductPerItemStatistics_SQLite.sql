with bought as (
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
)

, stolen as (
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
	where c.username = "Dieb"
	group by produktpalette_id
)

select
	b.produktpalette_id,
	b.name,
	b.anzahl,
	s.anzahl as stolen_anzahl,
	s.anzahl*1.0 / (s.anzahl + b.anzahl) * 100 as spec_stolen_anzahl,
	b.ek + s.ek as ek,
	b.vk as vk,
	b.vk - (b.ek + s.ek) as gewinn,
	(b.vk - (b.ek + s.ek))/b.anzahl as spec_gewinn,
	s.vk - s.ek as entg_gewinn,
	(s.vk - s.ek)/b.anzahl as spec_entg_gewinn
from bought b
join stolen s
	using (produktpalette_id)
order by b.name