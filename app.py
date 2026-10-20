#BY MALAOLU TIRENIOLUWA MOTOLARI
#This is the main application file for the Bincom test. 
# It uses Flask to create a web application that interacts with a SQLite database. 
# The application allows users to view polling unit results, calculate total results for an LGA, and add new polling unit results.
import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, g

app = Flask(__name__)
DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bincom.db")


# ---------- tiny database helpers ----------
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_FILE)
        g.db.row_factory = sqlite3.Row      # lets us use row["column_name"]
    return g.db


@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def query(sql, args=()):
    return get_db().execute(sql, args).fetchall()


def all_lgas():
    return query("SELECT lga_id, lga_name FROM lga ORDER BY lga_name")


# ---------- home ----------
@app.route("/")
def home():
    return render_template("home.html")


# ---------- QUESTION 1: result of one polling unit ----------
@app.route("/polling-unit")
def polling_unit_result():
    lga_id = request.args.get("lga", type=int)
    pu_id = request.args.get("pu", type=int)

    polling_units, pu, results = [], None, []
    if lga_id is not None:
        # chained combo box: only polling units of the chosen LGA
        polling_units = query(
            "SELECT uniqueid, polling_unit_name, polling_unit_number "
            "FROM polling_unit WHERE lga_id = ? ORDER BY polling_unit_name",
            (lga_id,))
    if pu_id is not None:
        pu = query("SELECT * FROM polling_unit WHERE uniqueid = ?", (pu_id,))[0:1]
        pu = pu[0] if pu else None
        # polling_unit_uniqueid is stored as text in this table
        results = query(
            "SELECT party_abbreviation, party_score FROM announced_pu_results "
            "WHERE polling_unit_uniqueid = ? ORDER BY party_score DESC",
            (str(pu_id),))
    return render_template("polling_unit.html", lgas=all_lgas(), lga_id=lga_id,
                           polling_units=polling_units, pu_id=pu_id, pu=pu,
                           results=results)


# ---------- QUESTION 2: summed total for an LGA ----------
@app.route("/lga-total")
def lga_total():
    lga_id = request.args.get("lga", type=int)
    totals, lga_name, grand_total, pu_count = [], None, 0, 0
    if lga_id is not None:
        row = query("SELECT lga_name FROM lga WHERE lga_id = ?", (lga_id,))
        lga_name = row[0]["lga_name"] if row else None
        # add up every polling unit that belongs to this LGA
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
                           grand_total=grand_total, pu_count=pu_count)


# ---------- QUESTION 3: store results for a new polling unit ----------
@app.route("/new-polling-unit", methods=["GET", "POST"])
def new_polling_unit():
    parties = query("SELECT partyid FROM party ORDER BY id")
    # the results table stores party codes as 4 characters (LABOUR -> LABO)
    codes = [p["partyid"][:4] for p in parties]
    message, error = None, None

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        number = request.form.get("number", "").strip()
        entered_by = request.form.get("entered_by", "").strip()
        lga_id = request.form.get("lga", type=int)

        scores = {}
        for code in codes:
            raw = request.form.get("score_" + code, "").strip()
            if raw == "" or not raw.isdigit():
                error = f"Please enter a whole number (0 or more) for {code}."
                break
            scores[code] = int(raw)

        if not error and (not name or not entered_by or lga_id is None):
            error = "Polling unit name, LGA and 'entered by' are required."

        if not error:
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
            for code, score in scores.items():
                db.execute(
                    "INSERT INTO announced_pu_results (polling_unit_uniqueid, "
                    "party_abbreviation, party_score, entered_by_user, date_entered, "
                    "user_ip_address) VALUES (?,?,?,?,?,?)",
                    (str(new_id), code, score, entered_by, now, ip))
            db.commit()                      # save everything together
            message = (f"Saved! '{name}' is polling unit #{new_id}. "
                       f"You can now find it under 'View a polling unit'.")

    return render_template("new_pu.html", lgas=all_lgas(), codes=codes,
                           message=message, error=error, form=request.form)


if __name__ == "__main__":
    app.run(debug=True)

#thank you, and I hoope to hear from you soon.