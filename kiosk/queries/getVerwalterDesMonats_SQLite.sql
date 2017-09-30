select
  first_name,
  last_name,
  username,
  sum(einkaufspreis)/100.0 as summeEingekauft,
  count(einkaufspreis) as anzahl
from (
	select
	  einkaufspreis,
	  verwalterEinpflegen_id,
	  geliefertUm
	from kiosk_gekauft

	union all

	select
	  einkaufspreis,
	  verwalterEinpflegen_id,
	  geliefertUm
	from kiosk_kiosk
	
) a
left join profil_kioskuser b
 on (a.verwalterEinpflegen_id = b.id)
where geliefertUm >= datetime(current_timestamp, '-1 month')
group by verwalterEinpflegen_id

order by summeEingekauft desc
limit 3