import param as pm


class PriceOracle(pm.Parameterized):
    price = pm.Dict({"USD": 1.0}, doc="maps a token to its equivalent value in USD")

    def __init__(self, price: dict=dict()):
        super().__init__()

        self.price.update(price)

    def convert(self, from_token: str, to_token: str="USD", n: float=1.0) -> float:
        """Converts the value of one token to another.

        \param from_token: the token to convert from.
        \param to_token: the token to converting to.
        \param n: the number of tokens to convert.
        """
        return n * self.price[from_token] / self.price[to_token]
