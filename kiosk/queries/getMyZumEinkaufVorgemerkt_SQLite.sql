select 
  b.id as id,
  b."produktName" as produktname,
  count(*) as "anzahlElemente",
  d.verkaufspreis * count(*) / 100.0 as einkaufspreis,
  ('input_id_angeliefert_' || b.id) as input_id_angeliefert,
  ('input_id_bezahlt_' || b.id) as input_id_bezahlt,
  e.kommentar as kommentar
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
join (
  select
    produktpalette_id,
    erstellt,
    kommentar
  from kiosk_produktkommentar
  join (
    select
      produktpalette_id,
      max(erstellt) as erstellt
    from kiosk_produktkommentar
    where erstellt < current_timestamp
    group by produktpalette_id  
  ) ua
  using(produktpalette_id,erstellt)
) e
  on b.id = e.produktpalette_id
where c.id = %s and b."imVerkauf" is true
group by b.id, b."produktName", d.verkaufspreis, b.id, b.id, e.kommentar
