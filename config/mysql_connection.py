import mysql.connector


def get_mysql_conn():
    conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='1234',
            database='PAYROLL'
        )
    return conn