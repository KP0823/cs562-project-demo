with t1 as (
	select cust, prod, avg(quant) one_avg_quant
	from sales
	where year=2018
	group by cust,prod
),
t2 as (
	select cust, prod, avg(quant) two_avg_quant
	from sales
	where year=2019
	group by cust,prod
),
t3 as (
	select cust, prod, avg(quant) three_avg_quant
	from sales
	where year=2020
	group by cust,prod
)
select t1.cust, t1.prod, one_avg_quant, two_avg_quant, three_avg_quant
from t1, t2, t3
where t1.cust= t2.cust and t2.cust= t3.cust and t1.prod= t2.prod and t1.prod= t3.prod
group by t1.cust, t1.prod, one_avg_quant, two_avg_quant, three_avg_quant
having three_avg_quant>= two_avg_quant and two_avg_quant>=one_avg_quant