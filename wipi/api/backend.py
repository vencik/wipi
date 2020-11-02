from typing import List, Dict, Tuple, Iterator
from json import dumps as jsonify
from threading import Thread
from queue import SimpleQueue as Queue, Empty as QueueEmpty
from multiprocessing import Pipe
from os import getpid
from multiprocessing.util import _exit_function as multiprocessing_exit_function
import atexit
from datetime import datetime
from functools import partial

from wipi.controller import Controller, controllers
from wipi.scheduler import Scheduler
from wipi.log import get_logger

from .shared_controller import SharedController


log = get_logger(__name__)


class Backend:
    """
    API backend
    """

    class Error(Exception):
        """
        Backend errors
        """

    def __init__(self, chunking_timeout: float = 20.0):
        """
        :param chunking_timeout: When downstreaming, generate connection "heartbeats"
                                 (by sending non-meaningful JSON white spaces)
                                 if connection is idle for this time [s]
        """
        self._chunking_timeout = chunking_timeout

        # Controllers (shared by all API workers)
        self._controllers: Dict[str, Controller] = {
            controller.name: SharedController(controller).start()
            for controller in controllers()
        }

        # Deferred actions scheduler
        self._scheduler = Scheduler(kwargs={"self": self}).start()

        # Master API worker PID (needed for correct shared resources shutdown)
        self._master_pid = getpid()

        # SharedController worker -> API worker communication pipe
        self._pipe: Tuple[Connection, Connection] = None

        log.info(f"Backend created")

    def worker_postfork(self) -> None:
        """
        uWSGI postfork hook
        The function is called after uWSGI forks the API workers.

        Creates SharedController worker results delivery pipe for this API worker.

        Deregisters MP exit function in forked API workers
        (so that they won't try to join child processes forked in master).
        """
        self._pipe = Pipe(duplex=False)

        if getpid() == self._master_pid:
            log.info("Master worker ready")

        else:  # forked worker
            atexit.unregister(multiprocessing_exit_function)
            log.info("Worker ready")

    def controllers(self) -> Dict[str, str]:
        """
        :return: List of enabled controllers' names and their types
        """
        return dict(
            (c.name, c.baseclass)
            for c in self._controllers.values())

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
                    "name" : cname,
                    "state" : self.get_state(cname),
                } for cname in self._controllers.keys()]
            }

        controller = self._get_ctrl(cname)
        return None if controller is None else controller.get_state(*self._pipe)

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
        return None if controller is None else controller.set_state(state, *self._pipe)

    def mute_set_state(self, cname: str = None, state: Dict = {}) -> None:
        """
        Set controller state discarding the result
        :param cname: Controller name on None
        :param state: State change
        """
        if cname is None:
            for controller in state["controllers"]:
                self.mute_set_state(controller["name"], controller["state"])
        else:
            controller = self._get_ctrl(cname)
            if controller is not None:
                controller.mute_set_state(state)

    def set_state_deferred(self, cname: str = None, state: Dict = {}) -> None:
        """
        Set controller state later
        :param when: Schedule
        :param cname: Controller name or None
        :param state: State change
        """
        def dt_spec2dt(dt_spec) -> datetime:
            return datetime.strptime(dt_spec, "%Y/%m/%d %H:%M:%S")

        at_spec: Union[str, List[str]] = state.pop("at") if "at" in state else None
        repeats: List[Dict] = state.pop("repeat") if "repeat" in state else []
        if cname:
            state = state.get("state", {})

        # Execution times
        at: List[datetime] = None
        if at_spec is not None:
            if type(at_spec) is str:
                at = [dt_spec2dt(at_spec)]
            elif type(at_spec) is list:
                at = [dt_spec2dt(dt_spec) for dt_spec in at_spec]
            else:
                raise Backend.Error(f"Invalid date-time specification: {at_spec}")

        task = Scheduler.Task(
            partial(Backend.mute_set_state, cname=cname, state=state), at)

        # Repetitions
        for repeat in repeats:
            times: Union[int, str] = repeat.get("times")
            interval = float(repeat.get("interval"))
            task.repeat("forever" if times is None else int(times), interval)

        self._scheduler.schedule(task)

    def list_deferred(self, cname: str = None) -> None:
        """
        Get list of deferred actions
        :param cname: Controller name
        """
        def dt2dt_spec(dt: datetime) -> str:
            return dt.strftime("%Y/%m/%d %H:%M:%S")

        tasks = self._scheduler.tasks(self._pipe)
        if cname is not None:
            tasks = [t for t in tasks if cname == t.action.keywords["cname"]]

        return [{
            "controller" : t.action.keywords["cname"],
            "state" : t.action.keywords["state"],
            "at" : [dt2dt_spec(dt) for dt in t.at],
        } for t in tasks]

    def cancel_deferred(self) -> None:
        """
        Cancel all scheduled deferred actions
        """
        self._scheduler.cancel()

    def _async_chunks(self, cgens: List[Tuple[str, Iterator[Dict]]]) -> Iterator[Dict]:
        """
        Generate chunks of (aggregate) response stream asynchronously
        :param cgens: Chunk data generators
        :return: JSON response chunks generator
        """
        queue = Queue()
        done = {}  # chunk generation done sentinel

        def gen_chunk(name: str, cgen: Iterator[Dict]) -> None:
            nonlocal queue
            nonlocal done
            for chunk in cgen:
                queue.put({"name": name, "data": chunk})
            queue.put(done)  # signal that we're finished

        threads = [
            Thread(target=gen_chunk, args=(name, cgen)) for name, cgen in cgens
        ]

        for thread in threads:
            thread.start()

        cgen_alive = len(threads)
        while cgen_alive > 0:
            try:
                chunk = queue.get(timeout=self._chunking_timeout)
                if chunk is done:
                    cgen_alive -= 1
                    continue

            except QueueEmpty:
                chunk = None  # interim chunk (used for connection heartbeats)

            yield chunk

        for thread in threads:
            thread.join()

    def _downstream_chunks(self, query: Dict, cname: str = None) -> Iterator[Dict]:
        """
        Downstream data chunks generator
        :param query: Downstream query
        :param cname: Constroller name or None
        :return: Downstream data chunks generator
        """
        if cname is None:
            return self._async_chunks(list(filter(lambda g: g is not None, (
                (ctrl["name"], self._downstream_chunks(ctrl["query"], ctrl["name"]))
                for ctrl in query["controllers"]))))

        controller = self._get_ctrl(cname)
        return None if controller is None else controller.downstream(query, *self_pipe)

    def downstream(self, cname: str = None, query: Dict = {}) -> Iterator[str]:
        """
        Downstream data

        Note that if streaming is requested by cname then the stream chunks
        are produced and sent by the uWSGI worker process directly.
        If controler(s) are queried in the query, worker threads are created
        for the chunks production and they are yielded asynchronously immediately
        when they're generated, sort of pell-mell.

        Also, in that case, connection keep-alive heartbeats (in form of harmless
        whitespaces in the JSON response) are sent should the connection remain
        inactive for longer than is safe to keep it alive.
        The same mechanism may be used by controllers themselves---by generating
        None chunk, the interim white space shall be sent.

        :param cname: Constroller name or None
        :param query: Downstream query
        :return: Downstream data chunks generator
        """
        separator = "["
        for chunk in self._downstream_chunks(query, cname):
            yield ' ' if chunk is None else separator + jsonify(chunk)
            separator = ", "

        yield "[]" if separator == "[" else "]"  # finish the JSON list stream

    def shutdown(self):
        """
        Shut backend down
        """
        if getpid() == self._master_pid:  # this worker is the master
            self._scheduler.stop()
            for controller in self._controllers.values():
                controller.stop()

            log.info("Master worker shut down")

        else:
            log.info("Worker shut down")

    def __del__(self):
        self.shutdown()
