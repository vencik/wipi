import re

_sc_re = re.compile(r'(?<!^)(?=[A-Z])')


def cc2sc(cc_str: str) -> str:
    """
    CamelCase -> snake_case
    :param cc_str: String in CamelCase
    :return: String in snake_case
    """
    return '.'.join([re.sub(_sc_re, '_', t).lower() for t in cc_str.split('.')])
