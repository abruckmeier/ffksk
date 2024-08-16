with plus as (
  select
    sum(betrag) as betragPlus,
    zunutzer_id as userID
  from kiosk_geldtransaktionen
  group by zunutzer_id
),

minus as (
  select
    sum(betrag) as betragMinus,
    vonnutzer_id as userID
  from kiosk_geldtransaktionen
  group by vonnutzer_id
)

select
  *
from plus a
left outer join minus b