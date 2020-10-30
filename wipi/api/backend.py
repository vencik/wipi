from typing import List, Dict, Tuple, Iterator
from json import dumps as jsonify
from threading import Thread
from queue import SimpleQueue as Queue, Empty as QueueEmpty
from multiprocessing import Pipe
from os import getpid
from multiprocessing.util import _exit_function as multiprocessing_exit_function
import atexit

from wipi.controller import Controller, controllers

from .shared_controller import SharedController


class Backend:
    """
    API backend
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

        # Master API worker PID (needed for correct shared resources shutdown)
        self._master_pid = getpid()

        # SharedController worker -> API worker communication pipe
        self._pipe: Tuple[Connection, Connection] = None

    def worker_postfork(self) -> None:
        """
        uWSGI postfork hook
        The function is called after uWSGI forks the API workers.

        Creates SharedController worker results delivery pipe for this API worker.

        Deregisters MP exit function in forked API workers
        (so that they won't try to join child processes forked in master).
        """
        self._pipe = Pipe(duplex=False)

        if getpid() != self._master_pid:
            atexit.unregister(multiprocessing_exit_function)

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
            for controller in self._controllers.values():
                controller.stop()

    def __del__(self):
        self.shutdown()
