select
	id,
	"aktivBis"
from profil_kioskuser a
where a."aktivBis" < current_timestamp + interval '7 days'
  --and a."aktivBis" >= datetime(current_timestamp)
  and a.visible is true
  and is_active is true
  and activity_end_msg = 0
