select
  b.*,
  a.verkaufspreis/100.0 as verkaufspreis,
  c."produktName",
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
where c.imVerkauf is 1
  and d.anzahl > 0
order by c."produktName" asc