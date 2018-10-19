select
	b.username,
	b.slackName,
	c.produktName,
	count(*) as anzahl
from kiosk_zumeinkaufvorgemerkt a
left join profil_kioskuser b
	on a.einkaeufer_id = b.id
left join kiosk_produktpalette c
	on a.produktpalette_id = c.id
where a."einkaufsvermerkUm" < datetime(current_timestamp, '-4 days')
group by username, produktName