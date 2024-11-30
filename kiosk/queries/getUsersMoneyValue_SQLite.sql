select
  sum(b.stand)/100.0 as value
from profil_kioskuser a
join kiosk_kontostand b
  on a.id = b.nutzer_id
where a.username not in ('kioskAdmin','Bargeld','Bank','Dieb','Bargeld_Dieb','Bargeld_im_Tresor','Gespendet','Spendenkonto','PayPal_Bargeld', 'Zuwendung')