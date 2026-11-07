import typing

# Define type variables for key and value to be used in the custom dictionary
K = typing.TypeVar("K")
V = typing.TypeVar("V")


class InformativeDict(typing.Dict[K, V], typing.Generic[K, V]):
    """A dictionary type that prints out the available keys."""

    def __getitem__(self, key: K) -> V:
        """Attempt to get item, raising a detailed exception if the key is not found."""
        try:
            return super().__getitem__(key)
        except KeyError:
            available_keys: typing.Iterable[str] = (str(k) for k in self.keys())
            raise KeyError(
                f"Key '{key}' not found. Available keys: {', '.join(available_keys)}"
            ) from None


class ReadOnlyInformativeDict(InformativeDict[K, V], typing.Generic[K, V]):
    """A read-only variant of the above."""

    def __setitem__(self, key: K, value: V) -> None:
        """Readonly object, setitem disallowed."""
        raise NotImplementedError("This dictionary is read-only")

    def __delitem__(self, key: K) -> None:
        """Readonly object, delitem disallowed."""
        raise NotImplementedError("This dictionary is read-only")

    def pop(self, *args: typing.Any, **kwargs: typing.Any) -> V:
        """Readonly object, pop disallowed."""
        raise NotImplementedError("This dictionary is read-only")

    def popitem(self) -> typing.Tuple[K, V]:
        """Readonly object, popitem disallowed."""
        raise NotImplementedError("This dictionary is read-only")

    def clear(self) -> None:
        """Readonly object, clear disallowed."""
        raise NotImplementedError("This dictionary is read-only")

    def update(self, *args: typing.Any, **kwargs: typing.Any) -> None:
        """Readonly object, update disallowed."""
        raise NotImplementedError("This dictionary is read-only")
