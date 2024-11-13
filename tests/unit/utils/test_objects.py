import abc
import collections.abc
import pickle
import typing
from collections.abc import Mapping, MutableMapping, MutableSet, Sequence, Set
from typing import ClassVar, Generic, Optional, Union
from unittest.mock import ANY, Mock

import pytest

from mode import Service, ServiceT
from mode.services import ServiceBase, ServiceCallbacks
from mode.utils.mocks import IN
from mode.utils.objects import (
    InvalidAnnotation,
    KeywordReduce,
    Unordered,
    _remove_optional,
    _restore_from_keywords,
    annotations,
    canoname,
    canonshortname,
    eval_type,
    guess_polymorphic_type,
    is_optional,
    is_union,
    iter_mro_reversed,
    label,
    qualname,
    remove_optional,
    shortname,
)

EXTRA_GENERIC_INHERITS_FROM = [abc.ABC]


class D(Service): ...


class C(D): ...


class B(C): ...


class A(B): ...


@pytest.mark.parametrize(
    "cls,stop,expected_mro",
    [
        (A, Service, [D, C, B, A]),
        (B, Service, [D, C, B]),
        (C, Service, [D, C]),
        (D, Service, [D]),
        (
            A,
            object,
            (
                [
                    ServiceCallbacks,
                    Generic,
                    *EXTRA_GENERIC_INHERITS_FROM,
                    ANY,
                    ServiceT,
                    ServiceBase,
                    Service,
                    D,
                    C,
                    B,
                    A,
                ]
            ),
        ),
        (A, B, [A]),
        (A, C, [B, A]),
        (A, D, [C, B, A]),
    ],
)
def test_iter_mro_reversed(cls, stop, expected_mro):
    assert list(iter_mro_reversed(cls, stop=stop)) == expected_mro


def test_Unordered():
    assert Unordered(1) < Unordered(10)
    x = set()
    x.add(Unordered({"foo": "bar"}))
    x.add(Unordered({"foo": "bar"}))
    assert len(x) == 2
    assert repr(x)


def test__restore_from_keywords():
    m = Mock()
    _restore_from_keywords(m, {"foo": 1, "bar": 20})
    m.assert_called_once_with(foo=1, bar=20)


class X(KeywordReduce):
    def __init__(self, name, age):
        self.name = name
        self.age = age

    def __reduce_keywords__(self):
        return {"name": self.name, "age": self.age}


def test_KeywordReduce():
    with pytest.raises(NotImplementedError):
        KeywordReduce().__reduce_keywords__()

    x = X("foo", 10)
    y = pickle.loads(pickle.dumps(x))
    assert y.name == x.name
    assert y.age == x.age


def test_qualname_object():
    class X: ...

    assert qualname("foo") == "builtins.str"
    assert qualname(str) == "builtins.str"

    assert qualname(X).endswith("test_qualname_object.<locals>.X")
    assert qualname(X()).endswith("test_qualname_object.<locals>.X")


def test_shortname_object():
    class X: ...

    assert shortname("foo") == "builtins.str"
    assert shortname(str) == "builtins.str"

    assert shortname(X) == __name__ + ".X"
    assert shortname(X()) == __name__ + ".X"


def test_canoname():
    class X: ...

    X.__module__ = "__main__"
    x = X()

    class Y: ...

    y = Y()

    assert canoname(X, main_name="faust") == "faust.test_canoname.<locals>.X"
    assert canoname(x, main_name="faust") == "faust.test_canoname.<locals>.X"
    assert canoname(Y, main_name="faust") == ".".join(
        [__name__, "test_canoname.<locals>.Y"]
    )
    assert canoname(y, main_name="faust") == ".".join(
        [__name__, "test_canoname.<locals>.Y"]
    )


def test_canonshortname():
    class X: ...

    X.__module__ = "__main__"
    x = X()

    class Y: ...

    y = Y()

    assert canonshortname(X, main_name="faust") == "faust.X"
    assert canonshortname(x, main_name="faust") == "faust.X"
    assert canonshortname(Y, main_name="faust") == ".".join([__name__, "Y"])
    assert canonshortname(y, main_name="faust") == ".".join([__name__, "Y"])


@pytest.mark.skip(reason="Needs fixing, typing.List eval does not work")
def test_eval_type():
    assert eval_type("list") == list  # noqa: E721
    assert eval_type("typing.List") == list  # noqa: E721


def test_annotations():
    class X:
        Foo: ClassVar[int] = 3
        foo: "int"
        bar: list["X"]
        baz: Union[list["X"], str]
        mas: int = 3

    fields, defaults = annotations(X, globalns=globals(), localns=locals())

    assert fields == {
        "Foo": ClassVar[int],
        "foo": int,
        "bar": list[X],
        "baz": Union[list[X], str],
        "mas": int,
    }
    assert defaults["mas"] == 3


def test_annotations__skip_classvar():
    class X:
        Foo: ClassVar[int] = 3
        foo: "int"
        bar: list["X"]
        baz: Union[list["X"], str]
        mas: int = 3

    fields, defaults = annotations(
        X, globalns=globals(), localns=locals(), skip_classvar=True
    )

    assert fields == {
        "foo": int,
        "bar": list[X],
        "baz": Union[list[X], str],
        "mas": int,
    }
    assert defaults["mas"] == 3


def test_annotations__invalid_type():
    class X:
        foo: list

    with pytest.raises(InvalidAnnotation):
        annotations(
            X,
            globalns=globals(),
            localns=locals(),
            invalid_types={list},
            skip_classvar=True,
        )


def test_annotations__no_local_ns_raises():
    class Bar: ...

    class X:
        bar: "Bar"

    with pytest.raises(NameError):
        annotations(X, globalns=None, localns=None)


# Union[type(None)] actually returns None
# so we have to construct this object to test condition in code.
WeirdNoneUnion = Union[str, int]
WeirdNoneUnion.__args__ = (type(None), type(None))


@pytest.mark.parametrize(
    "input,expected",
    [
        (Optional[str], str),
        (Union[str, None], str),
        (Union[str, type(None)], str),
        (Optional[list[str]], list[str]),
        (Optional[Mapping[int, str]], Mapping[int, str]),
        (Optional[Set[int]], Set[int]),
        (Optional[set[int]], set[int]),
        (Optional[tuple[int, ...]], tuple[int, ...]),
        (Optional[dict[int, str]], dict[int, str]),
        (Optional[list[int]], list[int]),
        (str, str),
        (list[str], list[str]),
        (Union[str, int, float], Union[str, int, float]),
        (WeirdNoneUnion, WeirdNoneUnion),
    ],
)
def test_remove_optional(input, expected):
    assert remove_optional(input) == expected


@pytest.mark.parametrize(
    "input,expected",
    [
        (Optional[str], ((), str)),
        (Union[str, None], ((), str)),
        (Union[str, type(None)], ((), str)),
        (Optional[list[str]], ((str,), list)),
        (
            Optional[Mapping[int, str]],
            ((int, str), IN(dict, collections.abc.Mapping, typing.Mapping)),
        ),
        (Optional[Set[int]], ((int,), IN(set, collections.abc.Set))),
        (Optional[set[int]], ((int,), IN(set, collections.abc.Set))),
        (Optional[tuple[int, ...]], ((int, ...), IN(tuple, tuple))),
        (Optional[dict[int, str]], ((int, str), dict)),
        (Optional[list[int]], ((int,), list)),
        (str, ((), str)),
        (list[str], ((str,), list)),
        (WeirdNoneUnion, ((type(None), type(None)), Union)),
    ],
)
def test__remove_optional__find_origin(input, expected):
    assert _remove_optional(input, find_origin=True) == expected


def test__remove_optional_edgecase():
    input = Union[str, int, float]
    expected = (str, int, float)
    res = _remove_optional(input, find_origin=True)
    assert res[0] == expected
    # must use `is` here on Python 3.6
    assert res[1] is typing.Union


@pytest.mark.parametrize(
    "input,expected",
    [
        (Optional[str], True),
        (Union[str, None], True),
        (Union[str, type(None)], True),
        (str, False),
        (list[str], False),
        (Union[str, int, float], False),
    ],
)
def test_is_optional(input, expected):
    assert is_optional(input) == expected


@pytest.mark.parametrize(
    "input,expected",
    [
        (tuple[int, ...], (tuple, int)),
        (list[int], (list, int)),
        (Mapping[str, int], (dict, int)),
        (dict[str, int], (dict, int)),
        (MutableMapping[str, int], (dict, int)),
        (set[str], (set, str)),
        (frozenset[str], (set, str)),
        (MutableSet[str], (set, str)),
        (Set[str], (set, str)),
        (Sequence[str], (list, str)),
    ],
)
def test_guess_polymorphic_type(input, expected):
    assert guess_polymorphic_type(input) == expected
    assert guess_polymorphic_type(Optional[input]) == expected
    assert guess_polymorphic_type(Union[input, None]) == expected


def test_guess_polymorphic_type__not_generic():
    class X: ...

    with pytest.raises(TypeError):
        guess_polymorphic_type(str)
    with pytest.raises(TypeError):
        guess_polymorphic_type(bytes)
    with pytest.raises(TypeError):
        guess_polymorphic_type(X)


def test_label_pass():
    s = "foo"
    assert label(s) is s


@pytest.mark.parametrize(
    "input,expected",
    [
        (str, False),
        (int, False),
        (Union[int, bytes], True),
        (Optional[str], True),
    ],
)
def test_is_union(input, expected):
    assert is_union(input) == expected
