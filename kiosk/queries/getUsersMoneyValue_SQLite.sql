select
  sum(b.stand)/100.0 as value
from profil_kioskuser a
join kiosk_kontostand b
  on a.id = b.nutzer_id
where a.id >= 5