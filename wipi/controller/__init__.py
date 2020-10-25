from typing import List, Dict, Iterator, Type
import json
import re
from importlib import import_module
from sys import argv

from .interface import Controller


_sc_re = re.compile(r'(?<!^)(?=[A-Z])')
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


def cc2sc(cc_str: str) -> str:
    """
    CamelCase -> snake_case
    :param cc_str: String in CamelCase
    :return: String in snake_case
    """
    return '.'.join([re.sub(_sc_re, '_', t).lower() for t in cc_str.split('.')])


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

        c1ass: Type[Controller] = getattr(
            import_module(cc2sc(class_name)),
            class_name.split('.')[-1])

        _controllers.append(c1ass(name, *args, **kwargs))


if len(argv) > 1:
    load_controllers(json.load(open(argv[1])))
