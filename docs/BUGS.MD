# Informal list of issues requiring attention
* see also the buglist for capfront.05

## Admin stuff
* Reset should be protected and only admin can do it
* Neither tokens nor hashed passwords should be exported in any endpoint
* Two standard users guest and admin should be initialised via the reset method
* Use .env file

## The simulation as such
### State (as viewed through 'Home') should be the same after a complete circuit as it was before. At present we see the following discrepancies:  
* The capitalists have not sold their capital services (which is correct, but we can't just let it accumulate just because nobody is buying it) THIS PROBLEM HAS RETURNED.  
* Unsold capital services should probably just go to waste.  
* Or we could have them sell these services to their own industries for nothing.  



## Crashes
API can't handle some bad requests. EG  

* GET /auth/login%26username%3Dguest%26password%3Dinsecure HTTP/1.1" 500 Internal Server Error  
results in    raise ResponseValidationError(
fastapi.exceptions.ResponseValidationError: 1 validation errors:
  {'type': 'model_attributes_type', 'loc': ('response',), 'msg': 'Input should be a valid dictionary or object to extract fields from', 'input': None, 'url': 'https://errors.pydantic.dev/2.5/v/model_attributes_type'}  



## DONE
* Demand should have been reduced to zero once trade has taken place, though we may want to keep note of the excess demand. DONE
* After Consumption, total value and price of labour power have not been recalculated for commodities. DONE  
* Classes stocks of consumption goods go negative after investment.  NO THEY DON'T  

