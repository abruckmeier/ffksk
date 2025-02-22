select distinct
  id,
  username,
  first_name,
  last_name,
  "slackName"
from profil_kioskuser u
join kiosk_zumeinkaufvorgemerkt v on u.id = v.einkaeufer_id
where is_active
  and "aktivBis" > current_timestamp
  and "instruierterKaeufer"
  and visible
