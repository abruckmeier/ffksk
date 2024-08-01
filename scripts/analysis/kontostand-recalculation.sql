with trans as (
select vonnutzer_id,
zunutzer_id,
sum(betrag) as stand
from kiosk_geldtransaktionen
group by vonnutzer_id, zunutzer_id
order by vonnutzer_id, zunutzer_id
)
SELECT * from trans order by vonnutzer_id

, von as (
select vonnutzer_id as id,
-sum(stand) as stand
from trans
group by vonnutzer_id
)

, zu as (
select zunutzer_id as id,
sum(stand) as stand
from trans
GROUP by zunutzer_id
)

select zu.id, 
coalesce(zu.stand,0) + coalesce(von.stand,0) as stand,
zu.stand as plus,
von.stand as minus
from zu
left join von using(id)
union all
select zu.id, 
coalesce(zu.stand,0) + coalesce(von.stand,0) as stand,
zu.stand as plus,
von.stand as minus
from von
left join zu using(id)
where zu.id is null