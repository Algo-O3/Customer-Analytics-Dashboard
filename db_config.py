"""
Database configuration file
Loads credentials securely from .env file
"""

import os
from dotenv import load_dotenv
from urllib.parse import quote_plus
import mysql.connector
from mysql.connector import Error, errorcode

load_dotenv()


DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'customer_analytics_project'),
    'port': int(os.getenv('DB_PORT', 3306))
}


def get_connection_string():

    user = quote_plus(DB_CONFIG['user'])
    password = quote_plus(DB_CONFIG['password']) if DB_CONFIG['password'] else ''
    host = DB_CONFIG['host']
    port = DB_CONFIG['port']
    database = DB_CONFIG['database']
  
    if password:
        connection_string = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
    else:
        connection_string = f"mysql+pymysql://{user}@{host}:{port}/{database}"
    
    return connection_string


def test_connection():

    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        
        if connection.is_connected():
            cursor = connection.cursor()
            cursor.execute("SELECT DATABASE();")
            database_name = cursor.fetchone()[0]
            
            cursor.execute("SELECT VERSION();")
            db_version = cursor.fetchone()[0]
            
            cursor.execute("SHOW TABLES;")
            tables = cursor.fetchall()
            table_count = len(tables)
            
            cursor.close()
            connection.close()
            
            success_message = f"""
Database Connection Successful! 

Connection Details:
   • Host: {DB_CONFIG['host']}
   • Port: {DB_CONFIG['port']}
   • User: {DB_CONFIG['user']}
   • Database: {database_name}
   • MySQL Version: {db_version}
   • Tables Found: {table_count}

"""
            return True, success_message
            
    except Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            error_message = f"""
Database Connection Failed!

Access Denied Error:
   Username or password is incorrect.

Test manually: mysql -u {DB_CONFIG['user']} -p
"""
            return False, error_message
            
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            error_message = f"""
Database Connection Failed!

 Database Does Not Exist:
   The database '{DB_CONFIG['database']}' was not found.



Current DB_NAME setting: {DB_CONFIG['database']}
"""
            return False, error_message
            
        else:
            error_message = f"""
Database Connection Failed!

MySQL Error ({err.errno}):
   {err}

"""
            return False, error_message
            
    except FileNotFoundError:
        error_message = f"""
 .env FILE NOT FOUND!                             

"""
        return False, error_message
            


if __name__ == "__main__":
    print("Testing Database Configuration...\n")
    
    success, message = test_connection()
    print(message)
    
    if success:
        print("Ready to run your applications!")
    else:
        print("Please fix the issues above before running the app.")