-- Kontostände aller Nutzer noch falsch
select
  a.username,
  b.stand/100.0
from profil_kioskuser a
join kiosk_kontostand b
  on a.id = b.nutzer_id


  -- Wert im Kiosk abfragen
with aaa as (
select
  c.id,
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
join kiosk_produktpalette c
    on a.produktpalette_id = c.id
)
select
  sum(verkaufspreis)/100.0
from kiosk_kiosk a
left join aaa b
 on a.produktpalette_id = b.id

 -- Eingekaufter Wert
 select
  date(gekauftUm) as datum,
  sum(verkaufspreis)/100.0
from kiosk_gekauft
group by datum
order by gekauftUm asc

-- fleißige Einkaeufer
select
  einkaeufer_id,
  username,
  sum(einkaufspreis)/100.0 as summeEingekauft
from (
	select
	  einkaufspreis,
	  einkaeufer_id
	from kiosk_gekauft

	union all

	select
	  einkaufspreis,
	  einkaeufer_id
	from kiosk_kiosk
) a
left join profil_kioskuser b
 on (a.einkaeufer_id = b.id)
group by einkaeufer_id

order by summeEingekauft desc

-- fleißige Nutzer
select
  kaeufer_id,
  username,
  sum(verkaufspreis)/100.0 as summeGekauft
from kiosk_gekauft a
left join profil_kioskuser b
 on (a.kaeufer_id = b.id)
group by kaeufer_id

order by summeGekauft desc

-- 