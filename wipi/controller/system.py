from typing import Dict

from . import Controller


class System(Controller):
    """
    Controller of the Raspberry Pi itself
    """

    def __init__(self, name: str):
        """
        :param name: Controller name
        """
        super().__init__(name)
        self._state: Dict = {
            "power": "on",
        }

    def _power(self, state: str) -> None:
        """
        Control power state
        :param state: "on"|"reboot"|"off"
        """
        if state == "off":
            print("TODO: Execute /sbin/shutdown -h now")

        elif state == "reboot":
            print("TODO: Execute /sbin/shutdown -r now")

        self._state["power"] = state

    def get_state(self) -> Dict:
        """
        :return: Current machine state
        """
        return self._state

    def set_state(self, state: Dict) -> Dict:
        """
        :param state: State change
        :return: Current machine state
        """
        power_state = state.get("power")
        if power_state is not None:
            self._power(power_state)

        return self.get_state()
