select
	b.username,
	b."slackName",
	c."produktName",
	count(*) as anzahl
from kiosk_zumeinkaufvorgemerkt a
left join profil_kioskuser b
	on a.einkaeufer_id = b.id
left join kiosk_produktpalette c
	on a.produktpalette_id = c.id
where a."einkaufsvermerkUm" < current_timestamp - interval '4 days'
group by b.username, b."slackName", c."produktName"
