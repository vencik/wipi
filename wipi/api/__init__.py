from flask import Flask

from .backend import Backend

backend = Backend()
app = Flask(__name__)

from . import routes
