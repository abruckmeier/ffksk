-------------------------------------------------
-- Zeitreihe
WITH RECURSIVE dates(datum) AS (
  VALUES('2017-07-15')
  UNION ALL
  SELECT date(datum, '+1 day')
  FROM dates
  WHERE datum < date('now')
)
--SELECT datum FROM dates
-------------------------------------------------

-------------------------------------------------
-- Bank
, bank as (
	with neg_transaktion as (
		select
			date(datum) as datum,
			sum(betrag) as betrag
		from kiosk_geldtransaktionen gt
		left join profil_kioskuser usr
			on usr.id = gt.vonnutzer_id
		where usr.username in ('Bank')
		group by date(datum)
	)
	--select * from neg_transaktion

	, pos_transaktion as (
		select
			date(datum) as datum,
			sum(betrag) as betrag
		from kiosk_geldtransaktionen gt
		left join profil_kioskuser usr
			on usr.id = gt.zunutzer_id
		where usr.username in ('Bank')
		group by date(datum)
	)
	--select * from pos_transaktion

	, stage_2 as (	
		select
			datum,
			coalesce(pt.betrag,0) as pos,
			coalesce(nt.betrag,0) as neg
		from dates
		left join pos_transaktion pt
			using(datum)
		left join neg_transaktion nt 
			using(datum)
	)
	--select * from stage_2

	, stage_1 as (	
		select
			datum,
			pos,
			(select sum(b2.pos) from stage_2 b2 where b2.datum <= b.datum ) as pos_kum,
			neg,
			(select sum(b2.neg) from stage_2 b2 where b2.datum <= b.datum ) as neg_kum
		from stage_2 b
	)
	
	select
		datum,
		pos_kum-neg_kum as stand
	from stage_1
	--select * from stage_1
)
-------------------------------------------------

-------------------------------------------------
-- Bargeld
, bargeld as (
	with neg_transaktion as (
		select
			date(datum) as datum,
			sum(betrag) as betrag
		from kiosk_geldtransaktionen gt
		left join profil_kioskuser usr
			on usr.id = gt.vonnutzer_id
		where usr.username in ('Bargeld', 'PayPal_Bargeld')
		group by date(datum)
	)
	--select * from neg_transaktion

	, pos_transaktion as (
		select
			date(datum) as datum,
			sum(betrag) as betrag
		from kiosk_geldtransaktionen gt
		left join profil_kioskuser usr
			on usr.id = gt.zunutzer_id
		where usr.username in ('Bargeld', 'PayPal_Bargeld')
		group by date(datum)
	)
	--select * from pos_transaktion

	, stage_2 as (	
		select
			datum,
			coalesce(pt.betrag,0) as pos,
			coalesce(nt.betrag,0) as neg
		from dates
		left join pos_transaktion pt
			using(datum)
		left join neg_transaktion nt 
			using(datum)
	)
	--select * from stage_2

	, stage_1 as (	
		select
			datum,
			pos,
			(select sum(b2.pos) from stage_2 b2 where b2.datum <= b.datum ) as pos_kum,
			neg,
			(select sum(b2.neg) from stage_2 b2 where b2.datum <= b.datum ) as neg_kum
		from stage_2 b
	)
	
	select
		datum,
		pos_kum-neg_kum as stand
	from stage_1
	--select * from stage_1
)
-------------------------------------------------

-------------------------------------------------
-- Bargeld im Tresor
, bargeld_tresor as (
	with neg_transaktion as (
		select
			date(datum) as datum,
			sum(betrag) as betrag
		from kiosk_geldtransaktionen gt
		left join profil_kioskuser usr
			on usr.id = gt.vonnutzer_id
		where usr.username in ('Bargeld_im_Tresor')
		group by date(datum)
	)
	--select * from neg_transaktion

	, pos_transaktion as (
		select
			date(datum) as datum,
			sum(betrag) as betrag
		from kiosk_geldtransaktionen gt
		left join profil_kioskuser usr
			on usr.id = gt.zunutzer_id
		where usr.username in ('Bargeld_im_Tresor')
		group by date(datum)
	)
	--select * from pos_transaktion

	, stage_2 as (	
		select
			datum,
			coalesce(pt.betrag,0) as pos,
			coalesce(nt.betrag,0) as neg
		from dates
		left join pos_transaktion pt
			using(datum)
		left join neg_transaktion nt 
			using(datum)
	)
	--select * from stage_2

	, stage_1 as (	
		select
			datum,
			pos,
			(select sum(b2.pos) from stage_2 b2 where b2.datum <= b.datum ) as pos_kum,
			neg,
			(select sum(b2.neg) from stage_2 b2 where b2.datum <= b.datum ) as neg_kum
		from stage_2 b
	)
	
	select
		datum,
		pos_kum-neg_kum as stand
	from stage_1
	--select * from stage_1
)
-------------------------------------------------

-------------------------------------------------
-- Bargeld Dieb
, bargeld_dieb as (
	with neg_transaktion as (
		select
			date(datum) as datum,
			sum(betrag) as betrag
		from kiosk_geldtransaktionen gt
		left join profil_kioskuser usr
			on usr.id = gt.vonnutzer_id
		where usr.username in ('Bargeld_Dieb')
		group by date(datum)
	)
	--select * from neg_transaktion

	, pos_transaktion as (
		select
			date(datum) as datum,
			sum(betrag) as betrag
		from kiosk_geldtransaktionen gt
		left join profil_kioskuser usr
			on usr.id = gt.zunutzer_id
		where usr.username in ('Bargeld_Dieb')
		group by date(datum)
	)
	--select * from pos_transaktion

	, stage_2 as (	
		select
			datum,
			coalesce(pt.betrag,0) as pos,
			coalesce(nt.betrag,0) as neg
		from dates
		left join pos_transaktion pt
			using(datum)
		left join neg_transaktion nt 
			using(datum)
	)
	--select * from stage_2

	, stage_1 as (	
		select
			datum,
			pos,
			(select sum(b2.pos) from stage_2 b2 where b2.datum <= b.datum ) as pos_kum,
			neg,
			(select sum(b2.neg) from stage_2 b2 where b2.datum <= b.datum ) as neg_kum
		from stage_2 b
	)
	
	select
		datum,
		pos_kum-neg_kum as stand
	from stage_1
	--select * from stage_1
)
-------------------------------------------------

-------------------------------------------------
-- Dieb
, dieb as (
	with neg_transaktion as (
		select
			date(datum) as datum,
			sum(betrag) as betrag
		from kiosk_geldtransaktionen gt
		left join profil_kioskuser usr
			on usr.id = gt.vonnutzer_id
		where usr.username in ('Dieb')
		group by date(datum)
	)
	--select * from neg_transaktion

	, pos_transaktion as (
		select
			date(datum) as datum,
			sum(betrag) as betrag
		from kiosk_geldtransaktionen gt
		left join profil_kioskuser usr
			on usr.id = gt.zunutzer_id
		where usr.username in ('Dieb')
		group by date(datum)
	)
	--select * from pos_transaktion

	, stage_2 as (	
		select
			datum,
			coalesce(pt.betrag,0) as pos,
			coalesce(nt.betrag,0) as neg
		from dates
		left join pos_transaktion pt
			using(datum)
		left join neg_transaktion nt 
			using(datum)
	)
	--select * from stage_2

	, stage_1 as (	
		select
			datum,
			pos,
			(select sum(b2.pos) from stage_2 b2 where b2.datum <= b.datum ) as pos_kum,
			neg,
			(select sum(b2.neg) from stage_2 b2 where b2.datum <= b.datum ) as neg_kum
		from stage_2 b
	)
	
	select
		datum,
		pos_kum-neg_kum as stand
	from stage_1
	--select * from stage_1
)
-------------------------------------------------

-------------------------------------------------
-- VK and EK value -> Marge
, marge as (
	with stage_3 as (
		select
			date("gekauftUm") as datum,
			sum(einkaufspreis) as ek,
			sum(verkaufspreis) as vk
		from kiosk_gekauft 
		group by date("gekauftUm")
	)
	--select * from stage_3

	, stage_2 as (	
		select
			datum,
			coalesce(pt.ek,0) as ek,
			coalesce(pt.vk,0) as vk
		from dates
		left join stage_3 pt
			using(datum)
	)
	--select * from stage_2

	, stage_1 as (	
		select
			datum,
			ek,
			(select sum(b2.ek) from stage_2 b2 where b2.datum <= b.datum ) as ek_sum,
			vk,
			(select sum(b2.vk) from stage_2 b2 where b2.datum <= b.datum ) as vk_sum
		from stage_2 b
	)
	
	select
		datum,
		vk_sum as vk,
		ek_sum as ek,
		vk_sum-ek_sum as marge
	from stage_1
	--select * from stage_1
)
-------------------------------------------------

select
	datum,
	marge.marge,
	marge.ek,
	marge.vk,
	bargeld_tresor.stand as bargeld_tresor,
	bank.stand,
	dieb.stand,
	bargeld_dieb.stand,
	bank.stand + dieb.stand - bargeld_dieb.stand as profit
from bank
join bargeld
	using(datum)
join bargeld_tresor
	using(datum)
join bargeld_dieb
	using(datum)
join dieb
	using(datum)
join marge
	using(datum)