# Capitalism 12.4
## Other documentation on this site: See docs folder.

## This is the front end for the simulation of a capitalist economy 
It builds on previous Django versions (see capitalism 11.8 and predecessors)  
But I have split the project into this backend and a separate front end  
As a result this project is pure Python, no Django  
I used fastAPI to create the API and SQLAlchemy to handle the ORM database operations  
It generates API endpoints which are read by a front end to display them  
Github project frontend, written in Go, is at https://github.com/axfreeman/capfront.03 (currently private so ask for access)  
The idea is that if you want, you can write your own front end  

# Installation and use brief suggestions  
To install, create virtual environment (assuming you want one) and pip install from ``requirements.txt``  
To run, enter ``uvicorn app.main:app `` or any other local development server  
Default port is 8000 - choose a different port if you don't want that  
To see the endpoints enter http://localhost:8000/docs (or use whichever port you created)  

## Further Notes on installation
These are more notes to self than guidelines at present  
* The database is initialized by the API endpoint /action/reset.  
  This reads standard data from json files in the static directory  
* There should always be two standard users, guest and admin. The frontend expects this.  
At present they are initialised by the clumsy method of registering them through the API.
'admin' should be registered first - a crude fix, because the user with id=1 gets access to all data but others only access data for simulations they have created.    
This should be automated, perhaps through the reset endpoint  

## Other notes

* There are no migration tools because there is no permanent database as yet. Therefore to change any model, the database should be removed and the app will create and initialize a new one.  
* When and if this is done, the developer should register the two standard users using Swagger. These are 'guest' and 'admin'. This initialization is not yet automatic.  
* Swagger can be used directly on the API but a user has to be logged in and the token applied in any GET requests. This can be done by using the Authorization key (at the top of the Swagger listing) and specifying 'bearer' authentication with the token.  
