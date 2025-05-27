select 
  b.id as product_id,
  c.id as user_id,
  b."produktName" as product_name,
  count(*) as max_number_elements,
  trunc(d.verkaufspreis * count(*) / 100.0, 2) as max_price
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
where c.id = %s and b."imVerkauf" is true
  and b.is_beverage is true
group by b.id, b."produktName", d.verkaufspreis, c.id
