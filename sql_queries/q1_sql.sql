with t1 as(
	select cust, sum(quant) NY_Sum
	from sales
	where state='NY'
	group by cust
),
t2 as (
	select cust, sum(quant) NJ_Sum
	from sales
	where state='NJ'
	group by cust
),
t3 as (
	select cust, sum(quant) CT_Sum
	from sales
	where state='CT'
	group by cust
)
select t1.cust, NY_Sum, NJ_Sum, CT_Sum
from t1, t2, t3
where t1.cust= t2.cust and t1.cust = t3.cust
group by t1.cust, NY_Sum, NJ_Sum, CT_Sum
having NY_Sum> 2 *NJ_Sum or NY_Sum > CT_Sum