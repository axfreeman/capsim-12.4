from ..models import Trace
from colorama import Fore,Back,Style

# Logging is principally to inform the user what's going on, so it's not logging as we know it
# As the simulation proceeds, create entries in the 'Trace' file which can be accesed via an endpoint

def report (level, simulation_id, message, session):
    colour=Fore.YELLOW
    if level>2:
        colour=Fore.GREEN
    elif level==2:
        colour=Fore.RED

    print(colour+" "* level + f"Level {level}: {message}"+Fore.WHITE)
    entry = Trace(
        simulation_id=simulation_id, 
        level=level, 
        time_stamp=1, #TODO this should come from the simulation, so actually, we probably don't need it
        message=message
        )
    session.add(entry)

