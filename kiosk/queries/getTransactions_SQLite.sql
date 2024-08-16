select * 
from (
    select 
      * 
    from (
        select
          "AutoTrans_ID",
          betrag as betrag,
          kommentar,
          datum
        from (
          select
            "AutoTrans_ID",
            -betrag/100.0 as betrag,
            kommentar,
           datum
          from kiosk_geldtransaktionen a
          where a.vonnutzer_id = %s

          union all

          select
            "AutoTrans_ID",
            betrag/100.0 as betrag,
            kommentar,
            datum
          from kiosk_geldtransaktionen a
          where a.zunutzer_id = %s
        ) uuua
      order by datum desc limit %s
    ) uua
    order by datum
    limit %s
  ) ua
order by datum desc