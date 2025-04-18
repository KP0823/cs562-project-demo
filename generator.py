import subprocess
import sys
import re
from collections import defaultdict

class mf_Query:
    def __init__(self):
        self.s=[]
        self.n=0
        self.V= []
        self.F=[]
        self.sigma=[]
        self.G=None

def readQuery_CommandLine():
    s= input("SELECT ATTRIBUTE(S):"). strip().lower().split(",")
    n= int(input("NUMBER OF GROUPING VARIABLES(n):").strip()) # this strip might be unnecessary
    V= input("GROUPING ATTRIBUTES(V):").strip().lower().split(",")
    F= input("F-VECT([F])").strip().lower().split(",")
    print("SELECT CONDITION-VECT:")
    counter =1
    sigma=[]
    while True:
        temp= input(f"{counter}.").strip().lower()
        if temp == "":
            break
        sigma.append(temp)
    G=input("HAVING_CONDITION(G):").strip().lower()

    return s, n, V, F, sigma, G

def readQuery_File(filename):
    with open(filename, 'r') as file:
        lines = file.readlines()
        s = lines[1].strip().lower().split(",")
        n = int(lines[3].strip())
        V = lines[5].strip().lower().split(",")
        F = lines[7].strip().lower().split(",")
        sigma = []
        for line in lines[9:]:
            if line[0].isdigit():
                sigma.append(line.strip().lower())
            else:
                break        
        G = lines[-1].strip().lower()
    return s, n, V, F, sigma, G

def adjusted_condtion(cond):
  splitString= re.split(r'\s*(or|and)\s*',cond)
  stripped_list= [item.strip() for item in splitString]
  result= []
  for item in stripped_list:
    if item.lower()=='or' or item.lower()=='and':
      result.append(item.lower())
    else:
      temp=re.split(r'\s*(==|<|>|!=|<=|>=)\s*',item)
      temp[0]= f'row[{temp[0]}]'
      result.append("".join(temp));
  return " ".join(result)
   

def main():
    #check if there is a file input
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        s, n, V, F, sigma, G = readQuery_File(filename)
        print(f"{s}\n {n}\n {V}\n {F}\n {sigma}\n {G}")
    else:
        s, n, V, F, sigma, G = readQuery_CommandLine()
        print(f"{s}\n {n}\n {V}\n {F}\n {sigma}\n {G}")

    """
    This is the generator code. It should take in the MF structure and generate the code
    needed to run the query. That generated code should be saved to a 
    file (e.g. _generated.py) and then run.
    """

    F = {"1_sum_quant", "2_sum_quant", "3_sum_quant", "3_avg_quant"}
    V = {"cust"}
    n = 3
    S = {"cust", "1_sum_quant", "2_sum_quant", "3_sum_quant"}
    sigma = ["state==NY", "state==NJ", "state==CT"]
    G = '1_sum_quant > 2 * 2_sum_quant or 1_avg_quant > 3_avg_quant'

    aggregates = defaultdict(lambda: defaultdict(set))
    for elem in F:
        x = elem.split('_')
        pass_idx, agg_func, attribute = int(x[0]), x[1], x[2]
        aggregates[pass_idx][agg_func].add(attribute)
    
    keys = ', '.join(f"'{v}': row['{v}']" for v in V)

    body = f"""
    mf_struct = {{}}
    rows = cur.fetchall()

    #pass 0
    for row in rows:
        key = tuple([{', '.join(f"row['{v}']" for v in V)}])
        if key not in mf_struct:
            mf_struct[key] = {{
            {keys},
            {', '.join(f"'avg_{i}_{attribute}_count': 0" for i in aggregates for func in aggregates[i] if func == 'avg' for attribute in aggregates[i][func])},
            {', '.join(f"'{i}_{func}_{attribute}': 0" for i in aggregates for func in aggregates[i] for attribute in aggregates[i][func])}
        }}

    #Passes to n
    """

    for i in range(1, int(n)+1):
        sigs = sigma[i-1]
        body += f"\n    #Pass {i}: Sigma is ({sigs})\n"
        body += "    for row in rows:\n"
        body += f"        if {adjusted_condtion(sigs)}:\n"
        body += f"            key = tuple([{', '.join(f'row[\"{v}\"]' for v in V)}])\n"

        for func in aggregates[i]:
            for attribute in aggregates[i][func]:
                if func == "sum":
                    body += f"            mf_struct[key]['{i}_sum_{attribute}'] += row['{attribute}']\n"
                elif func == "count":
                    body += f"            mf_struct[key]['{i}_count_{attribute}'] += 1\n"
                elif func == "avg":
                    body += f"            mf_struct[key]['{i}_avg_{attribute}'] += row['{attribute}']\n"
                    body += f"            mf_struct[key]['avg_{i}_{attribute}_count'] += 1\n"
                elif func == "max":
                    body += f"            mf_struct[key]['{i}_max_{attribute}'] = max(mf_struct[key]['{i}_max_{attribute}'], row['{attribute}'])\n"
                elif func == "min":
                    body += f"            if mf_struct[key]['{i}_min_{attribute}'] == 0 or row['{attribute}'] < mf_struct[key]['{i}_min_{attribute}']:\n"
                    body += f"                mf_struct[key]['{i}_min_{attribute}'] = row[{attribute}]\n"
        
    body += "\n#Compute Averages \n"
    for i in aggregates:
        for attribute in aggregates[i].get("avg", []):
            body += f"""
    for key in mf_struct:
        if mf_struct[key]['avg_{i}_{attribute}_count'] > 0:
            mf_struct[key]['{i}_avg_{attribute}'] /= mf_struct[key]['avg_{i}_{attribute}_count']
"""
        
    body += f"""
    _global = []
    for row in mf_struct.values():
        if {G}:
            _global.append({{key: row[key] for key in {S}}})
        """

    # Note: The f allows formatting with variables.
    #       Also, note the indentation is preserved.
    tmp = f"""
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
    {body}
    
    return tabulate.tabulate(_global,
                        headers="keys", tablefmt="psql")

def main():
    print(query())
    
if "__main__" == __name__:
    main()
    """
    readQuery_File("q1.txt");
    # Write the generated code to a file
    open("_generated.py", "w").write(tmp)
    # Execute the generated code
    subprocess.run(["python", "_generated.py"])


if "__main__" == __name__:
    main()
