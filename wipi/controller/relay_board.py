from typing import Dict

import RPi.GPIO as GPIO

from wipi.controller import Controller


class RelayBoard(Controller):
    """
    Controller for the RPi Relay Board (3 power relays expansion board).
    See https://www.waveshare.com/wiki/RPi_Relay_Board
    """

    # Relay I/O channel map
    _relays = {
        "relay1" : 26,
        "relay2" : 20,
        "relay3" : 21,
    }

    _states = {
        "open"   : GPIO.HIGH,
        "closed" : GPIO.LOW,
    }

    @staticmethod
    def _io_channel(relay: int) -> int:
        """
        Get relay I/O channel
        :param relay: Relay number
        :return: Relay I/O channel
        """
        return RelayBoard._relays[relay]

    @staticmethod
    def _io_state(state: str) -> int:
        """
        Relay state to GPIO state translation
        :param state: Relay state
        :return: GPIO state
        """
        return RelayBoard._states[state]

    def __init__(self, name: str, initial_state: str = "open"):
        super().__init__(name)
        self._initial_state = initial_state

        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)

        self._state: Dict[int, int] = dict()
        for relay, channel in RelayBoard._relays.items():
            self._state[relay] = self._initial_state
            GPIO.setup(
                channel, GPIO.OUT,
                initial=RelayBoard._io_state(self._initial_state))

    def _set_state(self, relay: int, state: str) -> None:
        """
        Set state of relay
        :param relay: Relay number
        :param state: Relay state
        """
        self._state[relay] = state
        GPIO.output(RelayBoard._io_channel(relay), RelayBoard._io_state(state))

    def get_state(self) -> Dict:
        """
        :return: Current relays state
        """
        return self._state

    def set_state(self, state: Dict) -> Dict:
        """
        :param state: State change
        :return: Current relays state
        """
        for relay, rstate in state.items():
            if relay not in self._state.keys():
                continue  # non-existing relay

            if rstate == self._state[relay]:
                continue  # nothing to do

            if rstate in RelayBoard._states:
                self._set_state(relay, rstate)

        return self.get_state()

    def __del__(self):
        for relay in self._state.keys():
            self._set_state(relay, self._initial_state)

        GPIO.cleanup()
