HOW TO RUN MY BINCOM PYTHON TEST SOLUTION 
BY MALAOLU TIRENIOLUWA MOTOLARI
IDE USED IS: VISUAL STUDIO CODE
PROGRAMMING LANGUAGE USED: PYTHON

Provided is a breakdown of how to run the code:
1. Save/download all the files in a folder then open in Visual Studio Code. The files to download are: app.py, setup_db.py, bincom_test.sql

2. then, inside that folder, create a folder named exactly "templates". LOWERCASE. Put these 5 files inside it: base.html, home.html, polling_unit.html, lga_total.html, new_pu.html
3. write "pip install flask" without the quotes in the terminal and press enter
4. run python setup_db.py (this will help us build bincom.db from bincom_test.sql, make sure you only run it once)
5. on the terminal type in "cd bincom" without the quotes and press enter
6. after, type this in the terminal "python app.py" without the quotes and press enter
7. open http://127.0.0.1:5000 on your browser

Each page consists of the answers to:

Question 1: "View a polling unit" - choose an LGA, then a polling unit, to see its result

Question 2: "LGA total" - choose an LGA to see the summed result of its polling units

Question 3: "Add polling unit" - store results for a new polling unit
