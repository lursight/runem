import typing

import pytest

from runem.informative_dict import InformativeDict, ReadOnlyInformativeDict

# Define type variables for key and value to be used in the custom dictionary
K = typing.TypeVar("K")
V = typing.TypeVar("V")


@pytest.fixture(name="sample_dict")
def sample_dict_fixture() -> InformativeDict[str, int]:
    """Test fixture for creating an instance of InformativeDict."""
    return InformativeDict({"one": 1, "two": 2, "three": 3})


def test_getitem_existing_key(sample_dict: InformativeDict[str, int]) -> None:
    assert (
        sample_dict["one"] == 1
    ), "Should retrieve the correct value for an existing key"


def test_getitem_non_existent_key(sample_dict: InformativeDict[str, int]) -> None:
    with pytest.raises(KeyError) as exc_info:
        _ = sample_dict["four"]
    assert "Key 'four' not found. Available keys: one, two, three" in str(
        exc_info.value
    ), "Should raise KeyError with a message listing available keys"


def test_iteration(sample_dict: InformativeDict[str, int]) -> None:
    keys = list(sample_dict)
    assert keys == [
        "one",
        "two",
        "three",
    ], "Iteration over dictionary should yield all keys"


def test_initialization_with_items() -> None:
    dict_init = InformativeDict({"a": 1, "b": 2})
    assert (
        dict_init["a"] == 1 and dict_init["b"] == 2
    ), "Should correctly initialize with given items"


def test_read_only_get_existing_key() -> None:
    """Test that accessing an existing key in ReadOnlyInformativeDict returns the
    correct value."""
    ro_dict = ReadOnlyInformativeDict[str, str]({"existing_key": "value"})
    assert (
        ro_dict["existing_key"] == "value"
    ), "Failed to retrieve the value for an existing key."


def test_read_only_get_non_existent_key() -> None:
    """Test that attempting to access a non-existent key in ReadOnlyInformativeDict
    raises a KeyError, and the error message includes the missing key and lists
    available keys."""
    ro_dict = ReadOnlyInformativeDict[str, str]({"existing_key": "value"})
    with pytest.raises(KeyError) as exc_info:
        _ = ro_dict["non_existent_key"]
    assert "non_existent_key" in str(
        exc_info.value
    ), "The exception message does not mention the missing key."
    assert "existing_key" in str(
        exc_info.value
    ), "The exception message does not list available keys."


# Define the operation type with concrete types for this test
OperationType = typing.Callable[..., None]


@pytest.mark.parametrize(
    "operation,args",
    [
        (lambda d, k, v: d.__setitem__(k, v), ("new_key", "new_value")),
        (lambda d, k, v: d.__delitem__(k), ("existing_key", None)),
        (lambda d, k, v: d.pop(k), ("existing_key", None)),
        (lambda d, k, v: d.popitem(), (None, None)),
        (lambda d, k, v: d.clear(), (None, None)),
        (lambda d, k, v: d.update({"another_key": "another_value"}), (None, None)),
    ],
)
def test_read_only_modification_operations_raise_error(
    operation: OperationType,
    args: typing.Tuple[typing.Optional[str], typing.Optional[str]],
) -> None:
    """Test that all modification operations on ReadOnlyInformativeDict (like setting an
    item, deleting an item, popping an item, clearing, and updating the dictionary)
    raise NotImplementedError.

    The test uses different operations and arguments to ensure comprehensive coverage.
    """
    ro_dict = ReadOnlyInformativeDict({"existing_key": "value"})
    with pytest.raises(NotImplementedError):
        operation(ro_dict, *args)
