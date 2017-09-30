  select 
	c."gruppenID" as gruppen_id,
	b."produktName" as produkt_name,
	d.kommentar as kommentar
  from
	kiosk_einkaufsliste a
  join kiosk_produktpalette b
	on a.produktpalette_ID = b.ID
  join kiosk_einkaufslistegroups c
	on a."kiosk_ID" = c."einkaufslistenItem_id"
  join (
	  select
	    produktpalette_id,
	    erstellt,
	    kommentar
	  from kiosk_produktkommentar
	  join (
	    select
	      produktpalette_id,
	      max(erstellt) as erstellt
	    from kiosk_produktkommentar
	    where erstellt < current_timestamp
	    group by produktpalette_id  
	  )
	  using(produktpalette_id,erstellt)
  ) d
  on b.id = d.produktpalette_id
  where gruppenID = %s
  group by c."gruppenID", b."produktName"
