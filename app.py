#BY MALAOLU TIRENIOLUWA MOTOLARI
#This is the main application file for the Bincom test. 
# It uses Flask to create a web application that interacts with a SQLite database. 
# The application allows users to view polling unit results, calculate total results for an LGA, and add new polling unit results.

import os #this allows me to work with files and folders
import sqlite3 #this is for the database file
from datetime import datetime #this is for the date and time
from flask import Flask, render_template, request, g #this is for the flask web framework

app = Flask(__name__) #this is creating a new Flask application instance
DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bincom.db") #this is the path to the database file


#this helps to get a database connection
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_FILE) #this connects to the database file
        g.db.row_factory = sqlite3.Row #this allows me to access the columns by name instead of index
    return g.db #this returns the database connection


@app.teardown_appcontext #thisregisters a function to be called
def close_db(exc): #this closes the db connection
    db = g.pop("db", None) #this pops the db connection from the g object, if it exists
    if db is not None:
        db.close()


def query(sql, args=()): #this executes a query and returns the results
    return get_db().execute(sql, args).fetchall() #this executes the query and fetches all the results


def all_lgas(): #this returns a list of all LGAs in the database
    return query("SELECT lga_id, lga_name FROM lga ORDER BY lga_name") #this executes a query to get all LGAs and orders them by name


#home page
@app.route("/") #this is the home page route
def home(): #this is the home page function
    return render_template("home.html")


#QUESTION 1: the result of one polling unit
@app.route("/polling-unit")
def polling_unit_result():
    lga_id = request.args.get("lga", type=int) #this gets the lga id from the request arguments and converts it to an integer
    pu_id = request.args.get("pu", type=int) #this gets the polling unit id from the request arguments and converts it to an integer

    polling_units, pu, results = [], None, [] #this initializes the polling_units, pu, and results variables
    if lga_id is not None: #this checks if the lga_id is not None
        polling_units = query(
            "SELECT uniqueid, polling_unit_name, polling_unit_number "
            "FROM polling_unit WHERE lga_id = ? ORDER BY polling_unit_name",
            (lga_id,)) #this executes a query to get all polling units for the given lga_id and orders them by name
    if pu_id is not None:
        pu = query("SELECT * FROM polling_unit WHERE uniqueid = ?", (pu_id,))[0:1]
        pu = pu[0] if pu else None
        results = query(
            "SELECT party_abbreviation, party_score FROM announced_pu_results "
            "WHERE polling_unit_uniqueid = ? ORDER BY party_score DESC",
            (str(pu_id),))
    return render_template("polling_unit.html", lgas=all_lgas(), lga_id=lga_id,
                           polling_units=polling_units, pu_id=pu_id, pu=pu,
                           results=results) #this renders the polling_unit.html template with the lgas, lga_id, polling_units, pu_id, pu, and results variables


#QUESTION 2: the summed total for an LGA
@app.route("/lga-total")
def lga_total():
    lga_id = request.args.get("lga", type=int)
    totals, lga_name, grand_total, pu_count = [], None, 0, 0 #this initializes the totals, lga_name, grand_total, and pu_count variables
    if lga_id is not None:
        row = query("SELECT lga_name FROM lga WHERE lga_id = ?", (lga_id,))
        lga_name = row[0]["lga_name"] if row else None #this gets the lga_name for the given lga_id
        totals = query(
            "SELECT r.party_abbreviation AS party, SUM(r.party_score) AS total "
            "FROM announced_pu_results r "
            "JOIN polling_unit p ON p.uniqueid = CAST(r.polling_unit_uniqueid AS INTEGER) "
            "WHERE p.lga_id = ? GROUP BY r.party_abbreviation ORDER BY total DESC",
            (lga_id,))
        grand_total = sum(t["total"] for t in totals)
        pu_count = query(
            "SELECT COUNT(DISTINCT r.polling_unit_uniqueid) AS n "
            "FROM announced_pu_results r "
            "JOIN polling_unit p ON p.uniqueid = CAST(r.polling_unit_uniqueid AS INTEGER) "
            "WHERE p.lga_id = ?", (lga_id,))[0]["n"]
    return render_template("lga_total.html", lgas=all_lgas(), lga_id=lga_id,
                           lga_name=lga_name, totals=totals,
                           grand_total=grand_total, pu_count=pu_count) #this renders the lga_total.html template with the lgas, lga_id, lga_name, totals, grand_total, and pu_count variables


#QUESTION 3: to store results for a new polling unit
@app.route("/new-polling-unit", methods=["GET", "POST"]) #this is the route for the new polling unit page, and it accepts both GET and POST requests
def new_polling_unit():
    parties = query("SELECT partyid FROM party ORDER BY id") #this executes a query to get all parties and orders them by id
    codes = [p["partyid"][:4] for p in parties]
    message, error = None, None #this initializes the message and error variables

    if request.method == "POST": #this checks if the request method is POST
        name = request.form.get("name", "").strip() #this gets the name from the form and strips any leading or trailing whitespace
        number = request.form.get("number", "").strip() #this gets the number from the form and strips any leading or trailing whitespace
        entered_by = request.form.get("entered_by", "").strip() 
        lga_id = request.form.get("lga", type=int)#this gets the lga_id from the form and converts it to an integer

        scores = {} #this initializes the scores dictionary
        for code in codes: #for loop
            raw = request.form.get("score_" + code, "").strip()
            if raw == "" or not raw.isdigit():
                error = f"Please enter a whole number (0 or more) for {code}."
                break
            scores[code] = int(raw) #this converts the raw score to an integer and adds it to the scores dictionary

        if not error and (not name or not entered_by or lga_id is None): #this checks if there is no error and if the name, entered_by, or lga_id is missing
            error = "Polling unit name, LGA and 'entered by' are required."

        if not error: #this checks if there is no error
            db = get_db()
            next_pu_id = (db.execute("SELECT COALESCE(MAX(polling_unit_id),0)+1 "
                                     "FROM polling_unit WHERE lga_id = ?",
                                     (lga_id,)).fetchone()[0])
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ip = request.remote_addr
            cur = db.execute(
                "INSERT INTO polling_unit (polling_unit_id, ward_id, lga_id, uniquewardid, "
                "polling_unit_number, polling_unit_name, entered_by_user, date_entered, "
                "user_ip_address) VALUES (?,?,?,?,?,?,?,?,?)",
                (next_pu_id, 0, lga_id, None, number, name, entered_by, now, ip))
            new_id = cur.lastrowid
            for code, score in scores.items(): #for loop
                db.execute(
                    "INSERT INTO announced_pu_results (polling_unit_uniqueid, "
                    "party_abbreviation, party_score, entered_by_user, date_entered, "
                    "user_ip_address) VALUES (?,?,?,?,?,?)", #this inserts the new polling unit results into the announced_pu_results table
                    (str(new_id), code, score, entered_by, now, ip)) #this inserts the new polling unit results into the announced_pu_results table
            db.commit()                      
            message = (f"Saved! '{name}' is polling unit #{new_id}. "
                       f"You can now find it under 'View a polling unit'.") #this sets the message variable to a success message

    return render_template("new_pu.html", lgas=all_lgas(), codes=codes,
                           message=message, error=error, form=request.form)


if __name__ == "__main__": #this checks if the script is being run directly (not imported)
    app.run(debug=True) #this runs the app in debug mode

#thank you, and I hoope to hear from you soon.
