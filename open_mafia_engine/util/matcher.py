import warnings
from collections.abc import MutableMapping
from typing import Dict, Generic, TypeVar

with warnings.catch_warnings():
    warnings.simplefilter("ignore")

    from fuzzywuzzy import process  # Remove warning about performance

T = TypeVar("T")


class Matcher(MutableMapping, Generic[T]):
    """Base class for target matching.

    The base version only does exact matches, and throws KeyError if not found.
    (Essentially, just a `Dict[str, T]`)
    """

    def __init__(self, choices: Dict[str, T]):
        #
        self._choices: Dict[str, T] = {}
        # Make sure to check
        for k, v in choices.items():
            self[k] = v

    def match(self, query: str) -> T:
        """Tries to match `query` to your object."""
        return self._choices[query]

    @property
    def choices(self) -> Dict[str, T]:
        return dict(self._choices)

    @choices.setter
    def choices(self, v: Dict[str, T]):
        self._choices = dict(v)

    def __getitem__(self, key: str) -> T:
        if key in self._choices:
            return self._choices[key]
        return self.match(key)

    def __setitem__(self, key: str, value: T):
        self._choices[key] = value

    def __delitem__(self, key: str):
        del self._choices[key]

    def __iter__(self):
        return iter(self.choices)  # making a copy

    def __len__(self):
        return len(self._choices)


class MatcherLowercase(Matcher, Generic[T]):
    """Matches everything by `query.lower()`."""

    def __setitem__(self, key: str, value: T):
        self._choices[key.lower()] = value

    def match(self, query: str) -> T:
        return self._choices[query.lower()]


class FuzzyMatcher(Matcher, Generic[T]):
    """Fuzzy matcher, with a score cutoff, using `fuzzywuzzy`.

    Parameters
    ----------
    choices : Dict[str, T]
        Mapping of name to whatever you want.
    score_cutoff : int
        The minimum score to use.
        Default is 0, in which case we use the best match, even if it's bad.
        If set higher, `match()` may raise KeyError.
    use_lower : bool
        Whether to use str.lower() for keys and queries.
        This probably improves matching in real-world cases.
        Default is True.
    """

    def __init__(
        self,
        choices: Dict[str, T] = None,
        *,
        score_cutoff: int = 0,
        use_lower: bool = True
    ):
        self.score_cutoff = int(score_cutoff)
        self.use_lower = bool(use_lower)
        super().__init__(choices)

    def __setitem__(self, key: str, value: T):
        if self.use_lower:
            key = key.lower()
        self._choices[key] = value

    def match(self, query: str) -> T:
        if self.use_lower:
            query = query.lower()
        options = list(self._choices.keys())
        # see: https://github.com/seatgeek/fuzzywuzzy
        res = process.extractOne(query, options, score_cutoff=self.score_cutoff)
        if res is None:
            raise KeyError(query)
        return self._choices[res[0]]
