from collections import Counter
from collections.abc import Iterable


class Vocab:
    """Small Python implementation of the torchtext Vocab interface."""

    def __init__(self, tokens: list[str]):
        self._itos = list(tokens)
        self._stoi = {token: index for index, token in enumerate(self._itos)}
        self._default_index = None

    def __len__(self):
        return len(self._itos)

    def __contains__(self, token):
        return token in self._stoi

    def __getitem__(self, token):
        if token in self._stoi:
            return self._stoi[token]
        if self._default_index is None:
            raise RuntimeError(f"Token {token!r} not found and default index is not set")
        return self._default_index

    def __call__(self, tokens):
        return self.lookup_indices(tokens)

    def set_default_index(self, index):
        self._default_index = index

    def get_default_index(self):
        return self._default_index

    def lookup_indices(self, tokens):
        return [self[token] for token in tokens]

    def lookup_tokens(self, indices):
        return [self._itos[index] for index in indices]

    def get_itos(self):
        return list(self._itos)

    def get_stoi(self):
        return dict(self._stoi)


def build_vocab_from_iterator(
    iterator: Iterable[Iterable[str]],
    min_freq: int = 1,
    specials: list[str] | None = None,
    special_first: bool = True,
    max_tokens: int | None = None,
):
    counter = Counter(token for tokens in iterator for token in tokens)
    ordered_tokens = [
        token
        for token, frequency in sorted(counter.items(), key=lambda item: (-item[1], item[0]))
        if frequency >= min_freq
    ]

    unique_specials = list(dict.fromkeys(specials or []))
    ordered_tokens = [token for token in ordered_tokens if token not in unique_specials]
    tokens = unique_specials + ordered_tokens if special_first else ordered_tokens + unique_specials
    if max_tokens is not None:
        tokens = tokens[:max_tokens]
    return Vocab(tokens)


__all__ = ["Vocab", "build_vocab_from_iterator"]
