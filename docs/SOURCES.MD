## Sources for tutorials  
* See https://www.youtube.com/watch?v=0sOvCWFmrtA&t=19209s
* See https://www.datacamp.com/tutorial/introduction-fastapi-tutorial 
* and https://www.youtube.com/watch?v=bLJ9jNWza6Y&List=PL8VzFQ8k4U1L5QpSapVEzoSfob-4CR8zM&index=90&t=50s  

* Dockerising (experimental) see https://www.youtube.com/watch?v=p1dwLKAxUxA&list=PLy_6D98if3ULEtXtNSY_2qN21VCKgoQAE&index=24  
 
# Authorization sources and methodology  
Will now be updated to https://fastapi.tiangolo.com/tutorial/security/simple-oauth2/  
The login functions of my own frontend at capfront.05 simply passes requests through into this backend  
The frontend does no authentication except to store the token in a client cookie  

### Also see (descriptions are simply to remind me which is which):
* https://medium.com/@pradoshkumar.jena/session-based-authentication-with-fastapi-a-step-by-step-guide-ca19e98ce0f9  
* https://timberry.dev/posts/fastapi-with-apikeys/    Tim Berry very basic good start point  
* https://www.youtube.com/watch?v=xZnOoO3ImSY  Rufus (currently using this)
* https://www.youtube.com/watch?v=1y4Nk4gH53Y  Fast-API-JWT all in one place so easy to follow  
* https://www.youtube.com/watch?v=6hTRw_HK3Ts  PrettyPrinted  
* https://www.youtube.com/watch?v=5GxQ1rLTwaU  Akamai Developer (Tim)
* https://www.youtube.com/watch?v=0A_GCXBCNUQ  Eric Roby
* https://www.youtube.com/watch?v=7_3TnuQ4EVY  More thorough  
* https://www.youtube.com/watch?v=C92mjEKUfNQ  Includes CORS middleware  
### on the JWT process as such
* https://dev.to/abrichak/jwt-and-go-how-to-integrate-them-with-security-requirements-eh5
* https://zivukushingai.medium.com/everything-you-need-to-know-about-frontend-and-backend-authentication-ultimate-guide-7142a752249c
## Contra JWT
* https://gist.github.com/samsch/0d1f3d3b4745d778f78b230cf6061452  
* https://www.youtube.com/watch?v=pYeekwv3vC4  
* 
### More reading
* on the Users map see https://stackoverflow.com/questions/42605337/cannot-assign-to-struct-field-in-a-map  

# VARIOUS SOLUTIONS TO CLONING
* CLONE FUNCTION USING DICTIONARY https://stackoverflow.com/questions/28871406/how-to-clone-a-sqlalchemy-object-with-new-primary-key
## INLINE CODE
session.expunge(template)  # expunge the template from the session, releasing it so we can make a fresh copy  
make_transient(template)  # http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.make_transient  
session.add(template)  
## FUNKY SOLUTION
https://www.youtube.com/watch?v=7JlK9ac57SA  
https://lyz-code.github.io/blue-book/coding/python/sqlalchemy/  
* NOTE THE ORIGINAL HAS TYPO ERROR - non_pk_columns in one place and non_primary_key_columns in another, '..keys' instead of 'keys'  
This briefer version of the above is suggested on https://stackoverflow.com/questions/28871406/  how-to-clone-a-sqlalchemy-object-with-new-primary-key  
It has at least one distinct advantage, namely it works. 
I used it also because it is generic, so we don't have to repeat it for each model  

# Logging
* https://www.loggly.com/ultimate-guide/python-logging-basics/
* https://dev.to/tomas223/logging-tracing-in-python-fastapi-with-opencensus-a-azure-2jcm  
* https://stackoverflow.com/questions/76356190/disable-logging-for-fastapi-form-data

# Types
* https://mypy.readthedocs.io/en/stable/cheat_sheet_py3.html  
* https://docs.python.org/3/library/typing.html  
* 
