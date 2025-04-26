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
    s= set([item.strip().lower() for item in input("SELECT ATTRIBUTE(S):").split(",")])
    n= int(input("NUMBER OF GROUPING VARIABLES(n):").strip()) # this strip might be unnecessary
    V= set([item.strip().lower() for item in input("GROUPING ATTRIBUTES(V):").split(",")])
    F= set([item.strip().lower() for item in input("F-VECT([F]):").split(",")])
    print("SELECT CONDITION-VECT(write True if the GV has no conditions):")
    sigma=[]
    for i in range (n):
        temp= input(f"{i+1}.").strip()
        sigma.append(temp)
    G=input("HAVING_CONDITION(G):").strip().lower()

    return s, n, V, F, sigma, G

def readQuery_File(filename):
    with open(filename, 'r') as file:
        lines = file.readlines()
        s = [item.strip().lower() for item in lines[1].split(",")]
        n = int(lines[3].strip())
        V = set([item.strip().lower() for item in lines[5].split(",")])
        F = set([item.strip().lower() for item in lines[7].split(",")])
        sigma = []
        for line in lines[9:]:
            if line[0].isdigit():
                sigma.append(re.sub(r'^\d+\.', '',(line.strip())))
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
      if temp[0] == 'True':
          return True
      temp[0]= f'row["{temp[0]}"]'
      result.append("".join(temp))
  return " ".join(result)

import re

def wrap_tokens_with_row(expr):
    # Set of keywords/logical operators we don't want to wrap
    exclude_keywords = {'or', 'and', 'not', 'in', 'is', 'if', 'else', 'elif', 'True', 'False', 'None'}

    #Checking if expr is true
    if (expr) == 'true':
        return True

    # Protect string literals
    string_literals = re.findall(r"'[^']*'", expr)
    placeholders = [f"__str_{i}__" for i in range(len(string_literals))]
    for lit, ph in zip(string_literals, placeholders):
        expr = expr.replace(lit, ph)

    # Replace variable-like tokens
    def replacer(match):
        token = match.group(0)
        if token.isdigit() or token in exclude_keywords:
            return token
        return f'row["{token}"]'

    # Match: any word-like token that starts with a letter or _, or digit followed by _
    expr = re.sub(r'\b[a-zA-Z_]\w*|\b\d+_\w*', replacer, expr)

    # Restore string literals
    for ph, lit in zip(placeholders, string_literals):
        expr = expr.replace(ph, lit)

    return expr

   

def main():
    #check if there is a file input
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        S, n, V, F, sigma, G = readQuery_File(filename)
        #change S V and F to "sets?"
        print(f"{F}\n {V}\n {n}\n {S}\n {sigma}\n {G}")
    else:
        S, n, V, F, sigma, G = readQuery_CommandLine()
        print(f"{F}\n {V}\n {n}\n {S}\n {sigma}\n {G}")

    """
    This is the generator code. It should take in the MF structure and generate the code
    needed to run the query. That generated code should be saved to a 
    file (e.g. _generated.py) and then run.
    """

    # F = {"1_sum_quant", "1_avg_quant", "2_sum_quant", "3_sum_quant", "3_avg_quant"}
    # V = {"cust"}
    # n = 3
    # S = ["cust", "1_sum_quant", "2_sum_quant", "3_sum_quant"]
    # sigma = ["state=='NY'", "state=='NJ'", "state=='CT'"]
    # G = '1_sum_quant > 2 * 2_sum_quant or 1_avg_quant > 3_avg_quant'

    aggregates = defaultdict(lambda: defaultdict(set))
    for elem in F:
        x = elem.split('_')
        pass_idx, agg_func, attribute = int(x[0]), x[1], x[2]
        aggregates[pass_idx][agg_func].add(attribute)
    
    keys = ', '.join(f"'{v}': row['{v}']" for v in V)

    body = f"""
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
                outputArr.append(f"row['{{token}}']")
            else:
                outputArr.append(token)
        return ' '.join(outputArr)
    mf_struct = {{}}
    rows = cur.fetchall()

    #pass 0
    """
    avg_line = ', '.join(
        f"'avg_{i}_{attribute}_count': 0"
        for i in aggregates for func in aggregates[i]
        if func == 'avg'
        for attribute in aggregates[i][func]
    )
    body += f"""
    for row in rows:
        key = tuple([{', '.join(f"row['{v}']" for v in V)}])
        if key not in mf_struct:
            mf_struct[key] = {{
            {keys},
    """
    if avg_line:
            body += f"""        {avg_line},"""
    body += f"""
            {', '.join(f"'{i}_{func}_{attribute}': 0" for i in aggregates for func in aggregates[i] for attribute in aggregates[i][func])}
        }}
        """
    """
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
                    body += f"                mf_struct[key]['{i}_min_{attribute}'] = row['{attribute}']\n"
        
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
        print(row)
        if {wrap_tokens_with_row(G)}:
            output = {{}}
            for col in {S}:
                if col in row:
                    output[col] = row[col]
                else:
                    output[col] = eval(simplify_aggr(col), None, {{"row": row}})
            _global.append(output)
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
    #print(readQuery_File(".\queries\q1.txt"))

    # Write the generated code to a file
    open("_generated.py", "w").write(tmp)
    # Execute the generated code
    subprocess.run(["python", "_generated.py"])


if "__main__" == __name__:
    main()
