with t1 as (
	select prod, month, min(quant) min_quant
	from sales
	group by prod, month
),
t2 as (
	select prod, month, max(quant) max_quant
	from sales
	group by prod, month
),
t3 as (
	select prod, month, avg(quant) avg_quant
	from sales
	group by prod, month
)
select t1.prod, t1.month, min_quant, max_quant, avg_quant
from t1, t2, t3
where t1.prod = t2.prod and t1.prod = t3.prod and t1.month = t2.month and t1.month = t3.month
order by t1.prod, t1.month