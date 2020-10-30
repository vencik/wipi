import logging
from os import environ as env
from os.path import dirname
from pathlib import Path


_etc = dirname(__file__) + "/../etc"
_logging_config = env.get("WIPI_CONFIG", f"{_etc}/logging.ini")
if Path(_logging_config).is_file():
    import logging.config
    logging.config.fileConfig(_logging_config)
else:
    logging.basicConfig(
        format="%(asctime)s %(process)d %(levelname)s: %(message)s",
        level=logging.INFO)


get_logger = logging.getLogger
