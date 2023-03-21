from abc import ABC, abstractmethod, abstractproperty
from dataclasses import dataclass
from io import TextIOWrapper
from typing import List


@dataclass
class CLICommandOptions:
    file: TextIOWrapper
    min_distance: float
    verbose: bool


class CLICommand(ABC):
    @abstractproperty
    def message(self) -> str:
        pass

    @abstractmethod
    def execute(self, options: CLICommandOptions) -> List[str] | None:
        pass
