import pyodbc

def get_sqlserver_conn():
    conn = pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=localhost;"
        "DATABASE=HUMAN;"
        "UID=sa;"
        "PWD=1234;"
    )
    return conn
