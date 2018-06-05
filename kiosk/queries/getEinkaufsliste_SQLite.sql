select
  "gruppenID",
  "produktName",
  "anzahlElemente",
  cast('<p class="items">' || item || '</p>' as text) as paket
from (
		select
		  "gruppenID",
		  "produktName",
		  "anzahlElemente",
		  cast("produktName" || ' | ' || anzahlElemente as text) as item
		from (
			  select 
			    c."gruppenID",
			    b."produktName",
			    count(*) as anzahlElemente
			  from
			    kiosk_einkaufsliste a
			  join kiosk_produktpalette b
			    on a.produktpalette_ID = b.ID
			  join kiosk_einkaufslistegroups c
			    on a."kiosk_ID" = c."einkaufslistenItem_id"
			  where b.imVerkauf is 1
			  group by c."gruppenID", b."produktName"
		)
	)
--group by "gruppenID"
order by "gruppenID" asc