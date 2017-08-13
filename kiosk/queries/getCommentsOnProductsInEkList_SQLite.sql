  select 
	c."gruppenID" as gruppen_id,
	b."produktName" as produkt_name,
	b.kommentar
  from
	kiosk_einkaufsliste a
  join kiosk_produktpalette b
	on a.produktpalette_ID = b.ID
  join kiosk_einkaufslistegroups c
	on a."kiosk_ID" = c."einkaufslistenItem_id"
  where gruppenID = %s
  group by c."gruppenID", b."produktName"
