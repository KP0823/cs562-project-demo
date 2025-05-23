
import os
import psycopg2
import psycopg2.extras
import tabulate
from dotenv import load_dotenv

# DO NOT EDIT THIS FILE, IT IS GENERATED BY generator.py

def query():
    load_dotenv()

    user = os.getenv('USER')
    password = os.getenv('PASSWORD')
    dbname = os.getenv('DBNAME')

    conn = psycopg2.connect("dbname="+dbname+" user="+user+" password="+password,
                            cursor_factory=psycopg2.extras.DictCursor)
    cur = conn.cursor()
    cur.execute("SELECT * FROM sales")
    
    _global = []
    
    import re
    #function needed to wrap aggregate equations
    def simplify_aggr(str):
        tokens = re.split(r'(\W)', str)
        outputArr = []
        for token in tokens:
            token = token.strip()
            if not token:
                continue
            if re.match(r'^\d+_(sum|avg|max|min|count)_\w+$', token):
                outputArr.append(f"row['{token}']")
            else:
                outputArr.append(token)
        return ' '.join(outputArr)

    mf_struct = {}
    rows = cur.fetchall()

    #pass 0
    
    for row in rows:
        key = tuple([row['prod'], row['cust']])
        if key not in mf_struct:
            mf_struct[key] = {
            'prod': row['prod'], 'cust': row['cust'],
            'avg_1_quant_count': 0, 'avg_3_quant_count': 0, 'avg_2_quant_count': 0,
            '1_avg_quant': 0, '3_avg_quant': 0, '2_avg_quant': 0
        }
        
    #Pass 1: Sigma is (year == 2018)
    for row in rows:
        if row["year"]==2018:
            key = tuple([row["prod"], row["cust"]])
            mf_struct[key]['1_avg_quant'] += row['quant']
            mf_struct[key]['avg_1_quant_count'] += 1

    #Pass 2: Sigma is (year == 2019)
    for row in rows:
        if row["year"]==2019:
            key = tuple([row["prod"], row["cust"]])
            mf_struct[key]['2_avg_quant'] += row['quant']
            mf_struct[key]['avg_2_quant_count'] += 1

    #Pass 3: Sigma is (year == 2020)
    for row in rows:
        if row["year"]==2020:
            key = tuple([row["prod"], row["cust"]])
            mf_struct[key]['3_avg_quant'] += row['quant']
            mf_struct[key]['avg_3_quant_count'] += 1

#Compute Averages 

    for key in mf_struct:
        if mf_struct[key]['avg_1_quant_count'] > 0:
            mf_struct[key]['1_avg_quant'] /= mf_struct[key]['avg_1_quant_count']

    for key in mf_struct:
        if mf_struct[key]['avg_3_quant_count'] > 0:
            mf_struct[key]['3_avg_quant'] /= mf_struct[key]['avg_3_quant_count']

    for key in mf_struct:
        if mf_struct[key]['avg_2_quant_count'] > 0:
            mf_struct[key]['2_avg_quant'] /= mf_struct[key]['avg_2_quant_count']

    #Apply Having Condition and form output table 
    
    _global = []
    for row in mf_struct.values():
        if row["3_avg_quant"] >= row["2_avg_quant"] and row["2_avg_quant"] >= row["1_avg_quant"]:
            output = {}
            for col in ['cust', 'prod', '1_avg_quant', '2_avg_quant', '3_avg_quant']:
                if col in row:
                    output[col] = row[col]
                else:
                    output[col] = eval(simplify_aggr(col), None, {"row": row})
            _global.append(output)
        
    
    return tabulate.tabulate(_global,
                        headers="keys", tablefmt="psql")

def main():
    print(query())
    
if "__main__" == __name__:
    main()
    