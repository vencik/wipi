from typing import Dict


class Controller:
    """
    Raspberry Pi used as controller
    """

    def __init__(self):
        self._foo = "bar"

    def status(self) -> Dict:
        """
        :return: Controller status
        """
        return {
            "foo": self._foo,
        }
