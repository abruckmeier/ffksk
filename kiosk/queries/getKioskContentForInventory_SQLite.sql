select
  a.verkaufspreis as verkaufspreis_ct,
  c.id,
  ('count_id_' || c.id) as count_id_name,
  ('checkbutton_id_' || c.id) as checkbutton_id_name,
  c."produktName" as produkt_name,
  d.anzahl
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
join (
    select
    c."produktName",
    count(*) as anzahl
    from kiosk_kiosk a
    join kiosk_produktpalette c
    on a.produktpalette_id = c.id
    group by c."produktName"
  ) d
  using("produktName")
where c."imVerkauf" is true
order by c."produktName"
