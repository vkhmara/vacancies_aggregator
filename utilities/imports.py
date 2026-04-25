import pkgutil
import inspect
import importlib
from typing import TypeVar, Type

T = TypeVar("T")


def get_all_subclasses(
    base_class: Type[T],
    package_name: str,
) -> list[T]:
    subclasses = []

    package = importlib.import_module(package_name)
    for _, module_name, is_pkg in pkgutil.walk_packages(
        package.__path__, package.__name__ + "."
    ):
        if is_pkg:
            continue
        module = importlib.import_module(module_name)
        subclasses += [
            obj
            for _, obj in inspect.getmembers(module, inspect.isclass)
            if issubclass(obj, base_class) and obj is not base_class
        ]

    return subclasses
