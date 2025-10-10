from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeVar


@dataclass
class CommandMeta:
    cls: type["BaseCommand"]
    help: str
    configure_parser: Callable


REGISTRY: dict[str, "CommandMeta"] = {}


class BaseCommand:
    def __init__(self, args):
        self.args = args


T = TypeVar("T", bound=type[BaseCommand])


def register(name: str, *, help: str, configure_parser: Callable):
    def wrapper(cls: T) -> T:
        REGISTRY[name] = CommandMeta(cls=cls, help=help, configure_parser=configure_parser)
        return cls

    return wrapper
