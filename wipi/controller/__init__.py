from typing import List, Dict, Iterator, Type
import json
import re
from importlib import import_module
from sys import argv

from wipi.util import cc2sc

from .interface import Controller


_controllers: List[Controller] = []


def add(controller: Controller) -> None:
    """
    Add another controller instance
    :param controller: Controller instance
    """
    _controllers.append(controller)


def controllers() -> Iterator[Controller]:
    """
    :return: Controller instances
    """
    return iter(_controllers)


def load_controllers(config: Dict) -> None:
    """
    Load configured controllers
    :param config: Controllers configuration
    """
    for controller in config.get("controllers", []):
        if not controller.get("enabled", False):
            continue  # skip disabled/not explicitly enabled controller

        name = controller["name"]
        class_name = controller["class"]
        args = controller.get("args", [])
        kwargs = controller.get("kwargs", {})

        _controllers.append(getattr(
            import_module(cc2sc(class_name)),
            class_name.split('.')[-1])(name, *args, **kwargs))


if len(argv) > 1:
    load_controllers(json.load(open(argv[1])))
