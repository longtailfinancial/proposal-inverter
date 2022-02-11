import pytest

from parameterized.price_oracle import PriceOracle


@pytest.fixture
def oracle():
    oracle = PriceOracle(
        price={
            "ADA": 1.5,
            "SOL": 96
        }
    )

    return oracle


def test_convert_ADA_to_USD(oracle):
    assert oracle.convert("ADA") == 1.5
    assert oracle.convert("ADA", "USD") == 1.5
    assert oracle.convert("ADA", "USD", 42) == 63


def test_convert_SOL_to_ADA(oracle):
    assert oracle.convert("SOL", "ADA") == 64
    assert oracle.convert("SOL", "ADA", 42) == 2688
