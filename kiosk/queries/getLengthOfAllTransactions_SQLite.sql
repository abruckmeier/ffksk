select
  count(*) as numTransactions
from (
    select
      "AutoTrans_ID"
    from kiosk_geldtransaktionen a
    where a.vonnutzer_id = %s

    union all

    select
      "AutoTrans_ID"
    from kiosk_geldtransaktionen a
    where a.zunutzer_id = %s
  ) ua
