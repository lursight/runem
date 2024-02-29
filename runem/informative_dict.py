import typing

# Define type variables for key and value to be used in the custom dictionary
K = typing.TypeVar("K")
V = typing.TypeVar("V")


class InformativeDict(typing.Dict[K, V], typing.Generic[K, V]):
    """A dictionary type that prints out the available keys."""

    def __getitem__(self, key: K) -> V:
        """Attempt to retrieve an item, raising a detailed exception if the key is not
        found."""
        try:
            return super().__getitem__(key)
        except KeyError:
            available_keys: typing.Iterable[str] = (str(k) for k in self.keys())
            raise KeyError(
                f"Key '{key}' not found. Available keys: {', '.join(available_keys)}"
            ) from None
