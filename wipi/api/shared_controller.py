from __future__ import annotations
from typing import Dict, Iterator, Callable, Any
from abc import ABC, abstractmethod
from multiprocessing import Process, Pipe, Lock
from multiprocessing.connection import Connection

from wipi.controller import Controller
from wipi.log import get_logger


log = get_logger(__name__)


class SharedController(Controller):
    """
    Controller implementation wrapper, executing controller actions in a single
    wroker shared by all API workers.
    Allows for multiple API workers sharing a single controller instance.
    """

    class Task(ABC):
        """
        Task for the shared controller (interface)
        """
        @abstractmethod
        def execute(self, ctrl: Controller) -> None:
            """
            Execute task
            :param ctrl: Wrapped controller
            """

    class ResultTask(Task):
        """
        Task which gives result back
        """

        def __init__(self, pipe_we: Connection, *args, **kwargs):
            """
            :param pipe_we: Writing end of pipe (for results delivery)
            """
            self._pipe_we = pipe_we

        def send(self, result: Any) -> None:
            """
            Send task result
            :param result: Task result
            """
            self._pipe_we.send(result)

    class GetStateTask(ResultTask):
        """
        Execute get_state on the shared controller
        """

        def execute(self, ctrl: Controller) -> None:
            """
            Execute ctrl.get_state
            :param ctrl: Wrapped controller
            """
            self.send(ctrl.get_state())

    class SetStateTask(ResultTask):
        """
        Execute set_state on the shared controller
        """

        def __init__(self, pipe_we: Connection, state: Dict):
            """
            :param pipe_we: Writing end of pipe (for results delivery)
            :param state: State changes
            """
            super().__init__(pipe_we)
            self._state = state

        def execute(self, ctrl: Controller) -> None:
            """
            Execute ctrl.set_state
            :param ctrl: Wrapped controller
            """
            self.send(ctrl.set_state(self._state))

    class MuteSetStateTask(Task):
        """
        Execute set_state on the shared controller, discarding result
        """

        def __init__(self, state: Dict):
            """
            :param state: State changes
            """
            self._state = state

        def execute(self, ctrl: Controller) -> None:
            """
            Execute ctrl.set_state
            :param ctrl: Wrapped controller
            """
            ctrl.set_state(self._state)

    class DownstreamTask(ResultTask):
        """
        Execute downstream on the shared controller
        """

        def __init__(self, pipe_we: Connection, query: Dict):
            """
            :param pipe_we: Writing end of pipe (for results delivery)
            :param query: Streaming query
            """
            super().__init__(pipe_we)
            self._query = query

        def execute(self, ctrl: Controller):
            """
            Stream via the pipe, finish by sending None
            :param ctrl: Wrapped controller
            """
            for chunk in ctrl.downstream(self._query):
                self.send(chunk)
            self.send(None)

    def __init__(self, ctrl: Controller):
        """
        :param ctrl: Wrapped controller
        """
        super().__init__(ctrl.name, ctrl.baseclass)
        self._ctrl = ctrl

        rend, wend = Pipe(duplex=False)
        self._pipe_re = rend
        self._pipe_we = wend
        self._pipe_wl = Lock()
        self._worker = Process(
            name=f"{self.__class__.__name__}({self._ctrl.__class__.__name__}.{self._ctrl.name})",
            target=self._worker_routine)

        log.info(f"{self.baseclass}.{self.name}: Controller created")

    def _send(self, task: SharedController.Task) -> None:
        """
        Send task to worker over pipe
        Pipe writes are mutually exclusive.
        :param task: Worker task
        """
        self._pipe_wl.acquire()
        try:
            self._pipe_we.send(task)
        finally:
            self._pipe_wl.release()

    def start(self) -> SharedController:
        """
        Start worker
        :return: self
        """
        self._worker.start()
        log.info(f"{self.baseclass}.{self.name}: Controller started")

        return self

    def get_state(self, pipe_re: Connection, pipe_we: Connection) -> Dict:
        """
        Controlled device state getter
        :param pipe_re: Reading end of multiprocessing.Pipe
        :param pipe_we: Writing end of multiprocessing.Pipe
        :return: Current controlled device state
        """
        self._send(SharedController.GetStateTask(pipe_we))
        return pipe_re.recv()

    def set_state(self, state: Dict, pipe_re: Connection, pipe_we: Connection) -> Dict:
        """
        Controlled device state setter
        :param state: State changes
        :param pipe_re: Reading end of multiprocessing.Pipe
        :param pipe_we: Writing end of multiprocessing.Pipe
        :return: Current controlled device state
        """
        self._send(SharedController.SetStateTask(pipe_we, state))
        return pipe_re.recv()

    def mute_set_state(self, state: Dict) -> None:
        """
        Controlled device state setter (discards result)
        Used for deferred set_state actions.
        :param state: State changes
        """
        self._send(SharedController.MuteSetStateTask(state))

    def downstream(self, query: Dict, pipe_re: Connection, pipe_we: Connection) -> Iterator[Dict]:
        """
        Downstream data from the controller
        :param query: Query
        :param pipe_re: Reading end of multiprocessing.Pipe
        :param pipe_we: Writing end of multiprocessing.Pipe
        :return: Generator of data chunks
        """
        self._send(SharedController.DownstreamTask(pipe_we, query))
        while True:
            chunk = pipe_re.recv()
            if chunk is None:
                return

            yield chunk

    def stop(self):
        """
        Stop worker
        """
        self._send(None)  # worker shutdown trigger
        self._worker.join()
        log.info(f"{self.baseclass}.{self.name}: Controller stopped")

    def _worker_routine(self):
        """
        Controller wrapper worker routine
        """
        log.info(f"{self.baseclass}.{self.name}: Worker starts")

        try:
            while True:
                task = self._pipe_re.recv()
                if task is None:
                    break  # shutdown immediately

                assert isinstance(task, SharedController.Task)
                task.execute(self._ctrl)

        except KeyboardInterrupt:
            pass  # interrupted by SIGINT

        log.info(f"{self.baseclass}.{self.name}: Worker terminates")

    def __del__(self):
        if self._worker.is_alive():
            self.stop()
