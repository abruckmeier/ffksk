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
          where a."vonNutzer_id" = %s

          union all

          select
            "AutoTrans_ID",
            betrag/100.0 as betrag,
            kommentar,
            datum
          from kiosk_geldtransaktionen a
          where a."zuNutzer_id" = %s
        )
      order by datum desc limit %s
    ) 
    order by datum asc 
    limit %s
  )
order by datum desc