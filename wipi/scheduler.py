from __future__ import annotations
from typing import Callable, List, Union, Optional
from threading import Thread, Lock
from multiprocessing import Pipe
from functools import total_ordering
from heapq import heappush, heappop
from datetime import datetime, timedelta


class Scheduler:
    """
    Deferred actions scheduler
    Actions are executed in a separate worker at specified times.
    They may be added at any time.
    """

    @total_ordering
    class Task:
        """
        Scheduled task
        """

        def __init__(self,
            action: Callable[[], None],
            at: Union[datetime, List[datetime]] = None):
            """
            :param action: Executed action
            :param at: Time(s) of execution (at least one must be specified,
                       default is now)
            """
            self.action = action

            if at is None:
                at = datetime.now()
            self.at: List[datetime] = [at] if isinstance(at, datetime) else at
            assert len(self.at) > 0

            self._forever_interval: timedelta = None

        def repeat(self, times: Union[int, str], interval: float) -> Scheduler.Task:
            """
            Set task repetition

            Note that each call adds repetitions (based on the last scheduled
            execution time.

            Example:
                Scheduler.Task(now, my_fn).repeat(2, 5).repeat(1, 10).repeat("forever", 30)

            creates a task which will be executed, thus:
            now, now+5s, now+10s, now+20s and then forever more in interval of 30s.

            :param times: How many times should the task be repeated
                          (e.g. 3 means three repetitions, "forever" means forever)
            :param interval: Repetition interval [s]
            """
            interval_td = timedelta(seconds=interval)

            if type(times) is str:
                assert times == "forever"
                self._forever_interval = interval_td

            else:
                for _ in range(times):
                    self.at.append(self.at[-1] + interval_td)

            return self

        def execute(self) -> Optional[Scheduler.Task]:
            """
            Execute task
            :return: Task (for re-scheduling) or None
            """
            self.action()
            exec_time = self.at.pop(0)

            if len(self.at) > 0:
                return self  # still more scheduling times

            if self._forever_interval is not None:  # reschedule forever
                self.at.append(exec_time + self._forever_interval)
                return self

            return None

        def __eq__(self, other):
            return self.at[0] == other.at[0]

        def __ne__(self, other):
            return not self == other

        def __lt__(self, other):
            return self.at[0] < other.at[0]

    _shutdown = "shutdown"  # worker shutdown sentinel
    _cancel = "cancel"      # scheduled tasks cancelation sentinel

    def __init__(self):
        rend, wend = Pipe(duplex=False)

        self._pipe_re = rend
        self._pipe_we = wend
        self._pipe_wl = Lock()
        self._worker = Thread(
            name=self.__class__.__name__,
            target=self._worker_routine)

    def _send(self, msg: Union[Scheduler.Task, str]) -> None:
        """
        Send message to worker via the pipe
        multiprocessing.Pipe.send calls are mutually exclusive.
        :param msg: Message sent
        """
        self._pipe_wl.acquire()
        try:
            self._pipe_we.send(msg)
        finally:
            self._pipe_wl.release()

    def start(self) -> Scheduler:
        """
        Start scheduler worker
        :return: self
        """
        self._worker.start()
        return self

    def schedule(self, task: Scheduler.Task) -> None:
        """
        Schedule task
        :param task: Task
        """
        self._send(task)

    def cancel(self) -> None:
        """
        Cancel all scheduled tasks
        """
        self._send(Scheduler._cancel)

    def stop(self) -> None:
        """
        Stop scheduler worker
        """
        self._send(Scheduler._shutdown)
        self._worker.join()

    def _worker_routine(self) -> None:
        tasks: List[Scheduler.Task] = []

        timeout: float = None
        while True:
            # Poll for new tasks
            if self._pipe_re.poll(timeout=timeout):
                task = self._pipe_re.recv()

                # Sentinels
                if type(task) is str:
                    # Shut down
                    if task == Scheduler._shutdown:
                        break

                    # Cancel all scheduled tasks
                    if task == Scheduler._cancel:
                        tasks = []

                # Schedule task
                else:
                    assert isinstance(task, Scheduler.Task)
                    heappush(tasks, task)

            # An action is due
            else:
                while len(tasks) > 0 and tasks[0].at[0] <= datetime.now():
                    task = heappop(tasks).execute()

                    # Reschedule
                    if task is not None:
                        heappush(tasks, task)

            # Set polling timeout (i.e. time to earliest task execution)
            if len(tasks) > 0:
                timeout = (tasks[0].at[0] - datetime.now()).total_seconds()
            else:
                timeout = None

    def __del__(self):
        if self._worker.is_alive():
            self.stop()
