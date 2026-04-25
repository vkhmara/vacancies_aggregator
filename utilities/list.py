from itertools import chain
from typing import Iterable


def join_lists(lists: Iterable[list]) -> list:
    return list(chain(*lists))
