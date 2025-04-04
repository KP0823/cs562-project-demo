import subprocess

class mf_Query:
    def __init__(self):
        self.s=[]
        self.n=0
        self.V= []
        self.F=[]
        self.sigma=[]
        self.G=None
    mf_Query=mf_Query()

def readQuery_CommandLine():
    s= input("SELECT ATTRIBUTE(S):"). strip().lower().split(",")
    n= int(input("NUMBER OF GROUPING VARIABLES(n):").strip()) # this strip might be unnecessary
    V= input("GROUPING ATTRIBUTES(V):").strip().lower().split(",")
    F= input("F-VECT([F])").strip().lower().split(",")
    print("SELECT CONDITION-VECT:")
    counter =1;
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

def main():
    """
    This is the generator code. It should take in the MF structure and generate the code
    needed to run the query. That generated code should be saved to a 
    file (e.g. _generated.py) and then run.
    """

    body = """
    for row in cur:
        if row['quant'] > 10:
            _global.append(row)
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
