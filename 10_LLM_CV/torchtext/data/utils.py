from collections.abc import Callable


def get_tokenizer(tokenizer, language: str = "en") -> Callable[[str], list[str]]:
    """Return a tokenizer compatible with torchtext.data.utils.get_tokenizer."""
    if callable(tokenizer):
        return tokenizer

    if tokenizer in (None, "basic_english"):
        return lambda text: text.lower().strip().split()

    if tokenizer == "spacy":
        import spacy

        try:
            nlp = spacy.load(language)
        except OSError:
            language_code = language.split("_")[0]
            nlp = spacy.blank(language_code)
        return lambda text: [token.text for token in nlp.tokenizer(text)]

    raise ValueError(f"Unsupported tokenizer: {tokenizer!r}")


__all__ = ["get_tokenizer"]

