
      
    select
      count(*) as numTransactions
    from (
        select
          "AutoTrans_ID"
        from kiosk_geldtransaktionen a
        where a."vonNutzer_id" = %s

        union all

        select
          "AutoTrans_ID"
        from kiosk_geldtransaktionen a
        where a."zuNutzer_id" = %s
      )