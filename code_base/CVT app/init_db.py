from pathlib import Path                                                   #importing Path from pathlib obj oriented way to hangle file paths across various platforms improving portability
import sqlite3                                                             #importing sqlite3 for working with sqlite databases


#path setup

BASE_DIR = Path(__file__).resolve().parent                                 #base dir is the folder containing the script
DB_PATH = BASE_DIR / "my_database.sqlite"                                  #db path path to the sqlite database file to be created
SQL_CREATOR = BASE_DIR / "my_table_creator.sql"                            #sql creator path to the sql file that contain the commands for creating the database table

#initializing the database

def init_db(db_path = DB_PATH, creator_file = SQL_CREATOR):                 #using this function we initialize the data base - function has 2 arguments path to the database file and path to the sql file 
    if not creator_file.is_file():                                          #we check if the sql file exists or not - if not an error message will be displayed
        raise FileNotFoundError(f"sql file not found")
    

    sql_script = creator_file.read_text(encoding = "utf-8")                 #we read the entire sql file as a string, read_text comes with Path method , we also make sure that is properly encoded

    with sqlite3.connect(db_path) as conn:                                  #we connect to sqlite and execute the sql script - we open a connection to the database file if it does not exist a sqlite file is created - executescript runs the entire sqlite script this includes CREATE TABLE
        conn.executescript(sql_script)

    print(f"Database was created at: {db_path}")                            #this is just a confirmation message - also optional

#entry point

if __name__ == "__main__":                                                 #it works when the script is executed and it calls init_db with default arguments to create the database
    init_db()