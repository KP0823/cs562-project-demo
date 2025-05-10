with t1 as (
	select prod, month, sum(quant) one_sum_quant
	from sales
	group by prod, month
),
t2 as (
	select prod, month, sum(quant) two_sum_quant
	from sales 
	where year = 2020
	group by prod, month
)
select t1.prod, t1.month, one_sum_quant, two_sum_quant, one_sum_quant + two_sum_quant, (1.0*one_sum_quant+1.0*two_sum_quant)/(two_sum_quant)
from t1, t2
where t1.prod= t2.prod and t1.month=t2.month
group by t1.prod, t1.month, one_sum_quant, two_sum_quant
having two_sum_quant> 10000 and one_sum_quant >40000