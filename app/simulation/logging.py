from fastapi import Depends

from app.database import get_db
from ..models import Trace
from colorama import Fore, Back, Style
import logging

FORMAT = "%(levelname)s:%(message)s"
logging.basicConfig(format=FORMAT, level=logging.DEBUG)
from sqlalchemy.orm import Session


# Logs both to the console and
# As the simulation proceeds, create entries in the 'Trace' file which can be accesed via an endpoint


def report(level, simulation_id, message, db: Session):
    """
    Prints a message on the terminal (or other output if designated) AND
    exports it to the Trace database which makes it available to the user

    the parameter simulation_id ensures that it reaches the correct user
    TODO rather than passing db as parameter, obtain it from get_db
    """
    colour = Fore.YELLOW
    if level > 2:
        colour = Fore.GREEN
    elif level == 2:
        colour = Fore.RED

    user_message = " " * level + f"Level {level}: {message}"
    log_message = " " * level+colour + message + Fore.WHITE
    logging.info(log_message)
    entry = Trace(
        simulation_id=simulation_id,
        level=level,
        time_stamp=1,  # TODO this should come from the simulation, so actually, we probably don't need it
        message=user_message,
    )
    db.add(entry)
    db.commit()
