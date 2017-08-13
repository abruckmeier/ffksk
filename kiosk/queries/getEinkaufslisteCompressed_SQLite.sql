select
a."gruppenID" as gruppen_id,
a.kommentar as kommentar,
group_concat(a.out, ' & ') as einkaufspakete
from (
	select
	  a."gruppenID",
	  a.kommentar,
	  cast(a."produktName" || ' | ' || cast(a.anzahlelemente as text) || 
	    ' | <' || cast(a.verkaufspreis*a.anzahlelemente/100.00 as text) as text) as out
	from (
		select 
		  c."gruppenID",
		  b."produktName",
		  b.kommentar,
		  count(*) as anzahlElemente,
		  d.verkaufspreis
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
		group by c."gruppenID", b."produktName"
		order by b."produktName"
		) a
	) a
group by a."gruppenID"
order by a."gruppenID" asc