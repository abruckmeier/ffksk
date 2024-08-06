select
  c.id,
  c."produktName",
  a.verkaufspreis,
  a."preisAufstockung"
from kiosk_produktverkaufspreise a
join (
    select
      a.produktpalette_id,
      max(a."gueltigAb") as "gueltigAb"
    from kiosk_produktverkaufspreise a
    where
      a."gueltigAb" < current_timestamp
    group by a.produktpalette_id
  ) b
  using (produktpalette_id, "gueltigAb")
join kiosk_produktpalette c
  on a.produktpalette_id = c.id
where c."imVerkauf" is true
  and c.id = %s
order by c."produktName"
