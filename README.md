#Course Project: Job Application Tracker 

#Features
- Dashboard that has total applications, sorts the applications by status, the responses, average salary, and recent applications
- CRUD for companies, jobs, applications, and contacts
- JSON columns (jobs.requirements and applications.interview_data) store data as JSON, but you edit them with regular form fields instead of typing raw JSON
- Job Match: type your skills and see jobs ranked by the percentage of the skills that the user has plus the skills that they're missing

#database
Four tables: companies, jobs, applications, contacts, that are connected with foreign keys
schema.sql creates the tables and adds sample data

#Setup
Needed: Python 3.9 or higher and MySQL running locally

1. Clone the repo and open the folder
2. Create a virtual environment and install packages
```
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
```
3. Create the database
```
    mysql -u root -p < schema.sql
    or open the schema.sql file in MySQL Workbench and run the entire script
```
4. Set your MySQL password
```
   export DB_PASSWORD= 'your password'
```
5. Run the app
```
    python app.py
    open http://localhost:5001
