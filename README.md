# CS4221/CS5421: Interactive Relational Algebra

**Group 4**

## Descripton
TODO


## Installation

`pip3 install -r backend/requirements.txt`

TODO: Fill in for frontend

## Commands to run app
Please make sure backend is already running before running the frontend.

### To run the backend

`cd backend` from root of the repo.

**Setup DB:** (DB to be created only once)

  `sudo -i -u postgres psql`

  `create database ira;` 

  Quit from the `psql` prompt by  `\q`

**Run the server locally:**

`python3 manage.py runserver`

### To run the frontend
TODO: Fill in commands


## Note
To checkout the backend api: 

- Clone this repository.

- Run the backend app in your local machine.

- [Export](https://learning.postman.com/docs/getting-started/importing-and-exporting-data/#exporting-collections) the  [relevant postman collection](https://elements.getpostman.com/redirect?entityId=17271995-fb1500f7-97c0-4fac-a890-b549a4a924d8&entityType=collection).

- Load it in your desktop postman app.


## References
Backend:

Idea to use `pandas` package to use a csv file to populate the Postgres DB is from https://apoor.medium.com/quickly-load-csvs-into-postgresql-using-python-and-pandas-9101c274a92f


Datasets:

iris csv: 
https://gist.github.com/netj/8836201

products and  sales csv:
https://www.sqlservercentral.com/articles/join-two-csv-files-with-a-common-column
Note: Original dataset was delimited by semicolons, and this had been changed to commas.