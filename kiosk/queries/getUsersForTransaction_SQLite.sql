select *
from 
(
  select
    id,
    username,
    first_name,
    last_name,
    "slackName"
  from profil_kioskuser
  where is_active
    and "aktivBis" > current_timestamp
    and visible
	
  union all
  
  select
    id,
    username,
    first_name,
    last_name,
    "slackName"
  from profil_kioskuser
  where username in ('Bank','Bargeld_Dieb','Bargeld_im_Tresor','Bargeld','Spendenkonto','PayPal_Bargeld')
) ua
order by lower(username)
