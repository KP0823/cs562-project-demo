with t1 as(
	select cust, prod, avg(quant) q1_avg_quant
	from sales
	where month >=1 and month <=3
	group by cust, prod
),
t2 as(
	select cust, prod, avg(quant) q2_avg_quant
	from sales
	where month >=4 and month <=6
	group by cust, prod
),
t3 as(
	select cust, prod, avg(quant) q3_avg_quant
	from sales
	where month >=7 and month <=9
	group by cust, prod
),
t4 as(
	select cust, prod, avg(quant) q4_avg_quant
	from sales
	where month >=10 and month <=12
	group by cust, prod
),
t5 as(
	select cust, prod, avg(quant) avg_quant
	from sales
	group by cust, prod
)
select t1.cust, t1.prod, q1_avg_quant, q2_avg_quant, q3_avg_quant, q4_avg_quant, avg_quant
from t1, t2, t3, t4, t5
where t1.cust=t2.cust and t1.cust=t3.cust and t1.cust=t4.cust and t1.cust=t5.cust
	and t1.prod=t2.prod and t1.prod=t3.prod and t1.prod=t4.prod and t1.prod=t5.prod
group by t1.cust, t1.prod, q1_avg_quant, q2_avg_quant, q3_avg_quant, q4_avg_quant, avg_quant
