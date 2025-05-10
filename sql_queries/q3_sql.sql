select prod, month, min(quant), max(quant), avg(quant)
from sales
group by prod, month
order by prod, month