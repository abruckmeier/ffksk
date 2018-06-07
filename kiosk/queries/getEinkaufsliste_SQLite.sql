
  select 
	c."gruppenID" as "gruppenID",
	b."ID" as id,
	b."produktName" as "produktName",
	count(*) as anzahlElemente,
	d.verkaufspreis*count(*)/100.0 as verkaufspreis,
	e.kommentar as kommentar
  from
	kiosk_einkaufsliste a
  join kiosk_produktpalette b
	on a.produktpalette_ID = b.ID
  join kiosk_einkaufslistegroups c
	on a."kiosk_ID" = c."einkaufslistenItem_id"
	
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
	  using (produktpalette_ID)
	
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
	) e
	  on b.id = e.produktpalette_id
	
  where b.imVerkauf is 1
  group by c."gruppenID", b."produktName"

order by "gruppenID" asc