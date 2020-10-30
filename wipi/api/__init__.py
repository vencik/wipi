from flask import Flask
import uwsgi

from .backend import Backend

backend = Backend()
uwsgi.post_fork_hook = backend.worker_postfork
uwsgi.atexit = backend.shutdown

app = Flask(__name__)

from . import routes
