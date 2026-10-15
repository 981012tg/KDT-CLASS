from collections.abc import Iterable, Iterator


def _iter_split(dataset: Iterable, language_pair: tuple[str, str]) -> Iterator[tuple[str, str]]:
    source_language, target_language = language_pair
    for example in dataset:
        yield example[source_language], example[target_language]


def Multi30k(
    root: str = ".data",
    split: str | tuple[str, ...] = ("train", "valid", "test"),
    language_pair: tuple[str, str] = ("de", "en"),
):
    """Return Multi30k iterators with the torchtext 0.18 calling convention."""
    del root  # Hugging Face Datasets manages its own cache directory.

    from datasets import load_dataset

    split_aliases = {"valid": "validation"}
    dataset = load_dataset("bentrevett/multi30k")

    def make_iterator(split_name: str):
        resolved_split = split_aliases.get(split_name, split_name)
        return _iter_split(dataset[resolved_split], language_pair)

    if isinstance(split, str):
        return make_iterator(split)
    return tuple(make_iterator(split_name) for split_name in split)


__all__ = ["Multi30k"]

