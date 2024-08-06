select
  b.produktpalette_id,
  b.validSince,
  a.verkaufspreis/100.0 as verkaufspreis,
  (a.verkaufspreis + a."preisAufstockung")/100.0 as aufstockungspreis,
  c."produktName",
  d.anzahl,
  e.num_stolen,
  coalesce(d.anzahl,0) + coalesce(e.num_stolen,0) as ges_available
from kiosk_produktverkaufspreise a
join (
    select
    a.produktpalette_id,
    max(a."gueltigAb") as validSince
    from
    kiosk_produktverkaufspreise a
    where
    a."gueltigAb" < current_timestamp
    group by
    a.produktpalette_id
  ) b
  on a.produktpalette_id = b.produktpalette_id and a."gueltigAb" = b.validSince
join kiosk_produktpalette c
  on a.produktpalette_id = c.id
left join (
    select
    c."produktName",
    count(*) as anzahl
    from kiosk_kiosk a
    join kiosk_produktpalette c
    on a.produktpalette_id = c.id
    group by c."produktName"
  ) d
  using("produktName")
left join (
  select
    gkft.produktpalette_id as produktpalette_id,
    count(*) as num_stolen
  from kiosk_gekauft gkft
  join profil_kioskuser usr
    on usr.id = gkft.kaeufer_id
  where usr.username = 'Dieb'
  group by gkft.produktpalette_id
  ) e
  using(produktpalette_id)
where c."imVerkauf" is true
order by c."produktName"
