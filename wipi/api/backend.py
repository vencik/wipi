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

    def get_state(self, cname: str = None) -> Dict:
        """
        Get controller state
        :param cname: Controller name or None
        :return: Current constroller state or dict of (name, state) of all of them
        """
        if cname is None:
            return {
                "controllers" : [{
                    "name" : controller.name,
                    "state" : controller.get_state(),
                } for controller in self._controllers.values()]
            }

        controller = self._get_ctrl(cname)
        return None if controller is None else controller.get_state()

    def set_state(self, cname: str = None, state: Dict = {}) -> Dict:
        """
        Set controller state
        :param cname: Controller name or None
        :param state: State change
        :return: Current constroller state or dict of (name, state) of all of them
        """
        if cname is None:
            for controller in state["controllers"]:
                self.set_state(controller["name"], controller["state"])

            return self.get_state()

        controller = self._get_ctrl(cname)
        return None if controller is None else controller.set_state(state)
