from typing import Dict, Iterator
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

    def downstream(self, query: Dict) -> Iterator[Dict]:
        """
        Downstream data from the controller
        Generated data chunks shall be streamed to the API user as (incrementally
        appended) list of dicts (using chunked encoding on the HTTP level).
        Use incremental JSON parser (e.g. jsonslicer) as client to decode
        the response in online manner.

        Note that the default implementation provides en empty iterator.
        This way, Controller implementations which don't have anything to stream,
        won't have to implement the member function.
        :param query: Query
        :return: Generator of data chunks
        """
        return iter(())
