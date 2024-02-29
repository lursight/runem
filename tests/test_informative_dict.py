import pytest

from runem.informative_dict import InformativeDict


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
