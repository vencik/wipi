from typing import Dict
from abc import ABC, abstractmethod


class Controller(ABC):
    """
    Raspberry Pi used as controller of <specified by implementation>
    """

    def __init__(self, name: str):
        """
        :param name: Controller name
        """
        self.name = name

    @abstractmethod
    def get_state(self) -> Dict:
        """
        Controlled device state getter
        :return: Current controlled device state
        """

    @abstractmethod
    def set_state(self, state: Dict) -> Dict:
        """
        Controlled device state setter
        :param state: State changes
        :return: Current controlled device state
        """
