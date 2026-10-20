#APPLICANT: MALAOLU TIRENIOLUWA MOTOLARI
#I used Visual studio code as my IDE
#Here is the solution to the python questions code.
#Thank you for this amazing opportunity to showcase my skills. I hope you find my solution satisfactory.

import re #i will b using this to find insert lines
import sqlite3 #for the database file
import os #this allows me to work with files and folders
#importing the necessary libraries

HERE = os.path.dirname(os.path.abspath(__file__)) #this helps me search for the sql file in the current directory
SQL_FILE = os.path.join(HERE, "bincom_test.sql") #this is the path to the sql file I was given
DB_FILE = os.path.join(HERE, "bincom.db") #this is the path to the database file I will create

if not os.path.exists(SQL_FILE): #this checks if the sql file exists, if not it will raise an error
    raise SystemExit("Put bincom_test.sql in this folder: " + HERE) #this raises an error if the sql file is not found in the current directory

#this is the schema for the database, it creates the necessary tables for the application
SCHEMA = """
CREATE TABLE lga (uniqueid INTEGER PRIMARY KEY, lga_id INT, lga_name TEXT, state_id INT,
    lga_description TEXT, entered_by_user TEXT, date_entered TEXT, user_ip_address TEXT);
CREATE TABLE ward (uniqueid INTEGER PRIMARY KEY, ward_id INT, ward_name TEXT, lga_id INT,
    ward_description TEXT, entered_by_user TEXT, date_entered TEXT, user_ip_address TEXT);
CREATE TABLE polling_unit (uniqueid INTEGER PRIMARY KEY, polling_unit_id INT, ward_id INT,
    lga_id INT, uniquewardid INT, polling_unit_number TEXT, polling_unit_name TEXT,
    polling_unit_description TEXT, lat TEXT, long TEXT, entered_by_user TEXT,
    date_entered TEXT, user_ip_address TEXT);
CREATE TABLE party (id INTEGER PRIMARY KEY, partyid TEXT, partyname TEXT);
CREATE TABLE announced_pu_results (result_id INTEGER PRIMARY KEY, polling_unit_uniqueid TEXT,
    party_abbreviation TEXT, party_score INT, entered_by_user TEXT, date_entered TEXT,
    user_ip_address TEXT);
CREATE TABLE announced_lga_results (result_id INTEGER PRIMARY KEY, lga_name TEXT,
    party_abbreviation TEXT, party_score INT, entered_by_user TEXT, date_entered TEXT,
    user_ip_address TEXT);
"""

if os.path.exists(DB_FILE): #If an old file with the same name is lying around, this line of code will delete it so we begin with a clean database.
    os.remove(DB_FILE) #this deletes the old database file if it exists


db = sqlite3.connect(DB_FILE)#this is creating the new database file and then connecting to it

db.executescript(SCHEMA) #executes the schema

text = open(SQL_FILE, encoding="latin-1").read() #this opens the .sql file and reads all of it into one big piece of text, and latin-1 is the text file I used.
inserts = re.findall(r"INSERT INTO `\w+`.*?\);\n", text, flags=re.S) #this finds all the insert statements in the text.

wanted = ("lga", "ward", "polling_unit", "party",
          "announced_pu_results", "announced_lga_results") #here i am only pinpointing the tables i want to use in the database.


for stmt in inserts: #this is a for loop
    table = re.match(r"INSERT INTO `(\w+)`", stmt).group(1) #this finds the table name in the insert statement.

    if table in wanted: #this helps m e check if the table name is in the wanted tuple.
        db.executescript(stmt)#this executes

db.commit() #this commits the changes to the database

for t in wanted: #for loop
    n = db.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] # this counts the number of rows in each table and fetches the first row of the result
    print(f"{t:25} {n} rows") #this prints

db.close() #this closes the database connection

#thank you and i hope to hear from you soon.