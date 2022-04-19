import param as pm
import typing

from collections import defaultdict
from copy import deepcopy


T = typing.TypeVar("T", bound="Funds")


class Funds(pm.Parameterized):
    funds = pm.Dict(defaultdict(float), doc="maps a token to the number of tokens held")
    price = {"USD": 1.0}

    def __init__(self, funds: dict | T = dict(), price: dict = dict()):
        super().__init__()

        self.funds.update(funds)
        self.price.update(price)

    def convert(self, from_token: str, to_token: str = "USD", n: float = 1.0) -> float:
        return n * self.price[from_token] / self.price[to_token]

    def items(self):
        return self.funds.items()

    def keys(self):
        return self.funds.keys()

    def total_funds(self, to_token: str = "USD"):
        return sum(
            [
                self.convert(from_token, to_token, n_tokens)
                for from_token, n_tokens in self.funds.items()
            ]
        )

    def update(self, funds: dict | T = dict()):
        for key, value in funds.items():
            self.funds[key] = value

    def __negative(self, other: dict | T, factor: int = 1) -> bool:
        return any(
            [self.funds[token] + factor * other[token] < 0 for token in other.keys()]
        )

    def __add__(self, other: dict | T):
        funds = deepcopy(self)

        if self.__negative(other, factor=1):
            raise ValueError("Failed to add, funds cannot be negative")

        for token in other.keys():
            funds[token] = self.funds[token] + other[token]

        return funds

    def __iadd__(self, other: dict | T):
        return self + other

    def __sub__(self, other: dict | T):
        funds = deepcopy(self)

        if self.__negative(other, factor=-1):
            raise ValueError("Failed to subtract, funds cannot be negative")

        for token in other.keys():
            funds[token] = self.funds[token] - other[token]

        return funds

    def __isub__(self, other: dict | T):
        return self - other

    def __mul__(self, factor: int | float):
        if factor < 0:
            raise ValueError("Failed to multiply, funds cannot be negative")

        return Funds({key: value * factor for key, value in self.funds.items()})

    def __imul__(self, factor: int | float):
        return self * factor

    def __rmul__(self, factor: int | float):
        return self * factor

    def __truediv__(self, factor: int | float):
        if factor < 0:
            raise ValueError("Failed to divide, funds cannot be negative")

        return Funds({key: value / factor for key, value in self.funds.items()})

    def __itruediv__(self, factor: int | float):
        return self / factor

    def __rtruediv__(self, factor: int | float):
        if factor < 0:
            raise ValueError("Failed to divide, funds cannot be negative")

        return Funds({key: factor / value for key, value in self.funds.items()})

    def __lt__(self, other: dict | T):
        return all([self.funds[token] < other[token] for token in other.keys()])

    def __le__(self, other: dict | T):
        return all([self.funds[token] <= other[token] for token in other.keys()])

    def __eq__(self, other: dict | T):
        return all([self.funds[token] == other[token] for token in other.keys()])

    def __ne__(self, other: dict | T):
        return all([self.funds[token] != other[token] for token in other.keys()])

    def __ge__(self, other: dict | T):
        return all([self.funds[token] >= other[token] for token in other.keys()])

    def __gt__(self, other: dict | T):
        return all([self.funds[token] > other[token] for token in other.keys()])

    def __getitem__(self, key: str):
        return self.funds[key]

    def __setitem__(self, key: str, value: float):
        self.funds[key] = value
