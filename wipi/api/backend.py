from typing import List, Dict

from wipi.controller import Controller, controllers


class Backend:
    """
    API backend
    """

    def __init__(self):
        self._controllers: Dict[str, Controller] = {
            controller.name: controller
            for controller in controllers()
        }

    def controllers(self) -> List[str]:
        """
        :return: List of enabled controllers' names
        """
        return list(self._controllers.keys())

    def _get_ctrl(self, cname: str) -> Controller:
        """
        :param cname: Controller name
        :return: Controller or None if it doesn't exist
        """
        return self._controllers.get(cname)

    def get_state(self, cname: str) -> Dict:
        """
        Get controller state
        :param cname: Controller name
        :return: Current constroller state
        """
        controller = self._get_ctrl(cname)
        return None if controller is None else controller.get_state()

    def set_state(self, cname: str, state: Dict) -> Dict:
        """
        Set controller state
        :param cname: Controller name
        :param state: State change
        :return: Current constroller state
        """
        controller = self._get_ctrl(cname)
        return None if controller is None else controller.set_state(state)
