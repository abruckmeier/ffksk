select
	id,
	"aktivBis"
from profil_kioskuser a
where a."aktivBis" < datetime(current_timestamp, '+7 days')
  --and a."aktivBis" >= datetime(current_timestamp)
  and a.visible = 1
  and is_active = 1
  and activity_end_msg = 0