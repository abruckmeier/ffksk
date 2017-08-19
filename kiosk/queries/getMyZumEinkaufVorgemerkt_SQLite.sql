select 
  b.id as id,
  b."produktName" as produktname,
  count(*) as anzahlElemente,
  d.verkaufspreis * count(*) / 100.0 as einkaufspreis,
  b.kommentar as kommentar
from
  kiosk_zumEinkaufVorgemerkt a
join kiosk_produktpalette b
  on a.produktpalette_ID = b.ID
join profil_kioskuser c
  on a.einkaeufer_id = c.id
join
(
  select
    a.verkaufspreis,
    a.produktpalette_id
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
) d
  using(produktpalette_ID)
where c.id = %s
group by b."produktName"