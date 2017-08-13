select
  id,
  username,
  first_name,
  last_name,
  slackName
from profil_kioskuser
where is_active
  and aktivBis > current_timestamp
  and visible
order by lower(username)