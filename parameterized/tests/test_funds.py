import pytest

from parameterized.funds import Funds


@pytest.fixture
def funds():
    funds = Funds(funds={"ABC": 42}, price={"ABC": 1.5, "XYZ": 96})

    return funds


def test_price(funds):
    oracle = Funds()

    assert funds.price == oracle.price


def test_convert_ABC_to_USD(funds):
    assert funds.convert("ABC") == 1.5
    assert funds.convert("ABC", "USD") == 1.5
    assert funds.convert("ABC", "USD", 42) == 63


def test_convert_XYZ_to_ABC(funds):
    assert funds.convert("XYZ", "ABC") == 64
    assert funds.convert("XYZ", "ABC", 42) == 2688


def test_add(funds):
    assert funds + Funds() == {"ABC": 42}
    assert funds + {"ABC": 1, "XYZ": 2} == {"ABC": 43, "XYZ": 2}

    with pytest.raises(ValueError):
        funds + {"ABC": 1, "XYZ": -2}


def test_iadd(funds):
    funds += Funds()
    assert funds == {"ABC": 42}

    funds += {"ABC": 1, "XYZ": 2}
    assert funds == {"ABC": 43, "XYZ": 2}

    with pytest.raises(ValueError):
        funds += {"XYZ": -4}


def test_sub(funds):
    assert funds - Funds() == {"ABC": 42}
    assert funds - {"ABC": 1} == {"ABC": 41}

    with pytest.raises(ValueError):
        funds - {"ABC": 1, "XYZ": 2}


def test_isub(funds):
    funds -= Funds()
    assert funds == {"ABC": 42}

    funds -= {"ABC": 1}
    assert funds == {"ABC": 41}

    with pytest.raises(ValueError):
        funds -= {"ABC": 1, "XYZ": 2}


def test_mul(funds):
    assert funds * 2 == {"ABC": 84}

    with pytest.raises(ValueError):
        funds * -1


def test_imul(funds):
    funds *= 2

    assert funds == {"ABC": 84}

    with pytest.raises(ValueError):
        funds *= -1


def test_rmul(funds):
    assert 2 * funds == {"ABC": 84}

    with pytest.raises(ValueError):
        -1 * funds


def test_div(funds):
    assert funds / 2 == {"ABC": 21}

    with pytest.raises(ValueError):
        funds / -1


def test_idiv(funds):
    funds /= 2

    assert funds == {"ABC": 21}

    with pytest.raises(ValueError):
        funds /= -1


def test_rdiv(funds):
    assert 84 / funds == {"ABC": 2}

    with pytest.raises(ValueError):
        -1 / funds


def test_lt(funds):
    assert not funds < {"ABC": 40}
    assert not funds < {"ABC": 42}
    assert funds < {"ABC": 50}
    assert funds < {"XYZ": 1}


def test_le(funds):
    assert not funds <= {"ABC": 40}
    assert funds <= {"ABC": 42}
    assert funds <= {"ABC": 50}
    assert funds < {"XYZ": 1}


def test_eq(funds):
    assert not funds == {"ABC": 40}
    assert funds == {"ABC": 42}
    assert not funds == {"ABC": 50}
    assert not funds == {"XYZ": 1}


def test_ne(funds):
    assert funds != {"ABC": 40}
    assert not funds != {"ABC": 42}
    assert funds != {"ABC": 50}
    assert funds != {"XYZ": 1}


def test_ge(funds):
    assert funds >= {"ABC": 40}
    assert funds >= {"ABC": 42}
    assert not funds >= {"ABC": 50}
    assert not funds >= {"XYZ": 1}


def test_gt(funds):
    assert funds > {"ABC": 40}
    assert not funds > {"ABC": 42}
    assert not funds > {"ABC": 50}
    assert not funds > {"XYZ": 1}


def test_getitem(funds):
    assert funds["ABC"] == 42
    assert funds["XYZ"] == 0


def test_setitem(funds):
    funds["XYZ"] = 1

    assert funds["ABC"] == 42
    assert funds["XYZ"] == 1
