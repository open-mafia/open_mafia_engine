from typing import Union
from .base import StateModel


class StatusItem(StateModel):
    """Defines a single status.
    
    Attributes
    ----------
    key : str
        String
    """

    key: str
    value: Union[bool, int, float, str]
