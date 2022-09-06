from __future__ import annotations
# built-in
from collections import Counter
from contextlib import suppress

# app
from ..libraries import prototype
from ..utils import find_ngrams


libraries = prototype.clone()
libraries.optimize()


class Base:
    def __init__(self, qval: int = 1, external: bool = True) -> None:
        self.qval = qval
        self.external = external

    def __call__(self, *sequences) -> float:
        raise NotImplementedError

    @staticmethod
    def maximum(*sequences) -> float:
        """Get maximum possible value
        """
        return max(map(len, sequences))

    def distance(self, *sequences) -> float:
        """Get distance between sequences
        """
        return self(*sequences)

    def similarity(self, *sequences) -> float:
        """Get sequences similarity.

        similarity = maximum - distance
        """
        return self.maximum(*sequences) - self.distance(*sequences)

    def normalized_distance(self, *sequences) -> float:
        """Get distance from 0 to 1
        """
        maximum = self.maximum(*sequences)
        if maximum == 0:
            return 0
        return self.distance(*sequences) / maximum

    def normalized_similarity(self, *sequences) -> float:
        """Get similarity from 0 to 1

        normalized_similarity = 1 - normalized_distance
        """
        return 1 - self.normalized_distance(*sequences)

    def external_answer(self, *sequences) -> float | None:
        """Try to get answer from known external libraries.
        """
        # if this feature disabled
        if not getattr(self, 'external', False):
            return None
        # all external libs don't support test_func
        test_func = getattr(self, 'test_func', self._ident)
        if test_func is not self._ident:
            return None
        # try to get external libs for algorithm
        libs = libraries.get_libs(self.__class__.__name__)
        for lib in libs:
            # if conditions not satisfied
            if not lib.check_conditions(self, *sequences):
                continue
            # if library is not installed yet
            func = lib.get_function()
            if func is None:
                continue
            prepared_sequences = lib.prepare(*sequences)
            # fail side libraries silently and try next libs
            with suppress(Exception):
                return func(*prepared_sequences)
        return None

    def quick_answer(self, *sequences) -> float | None:
        """Try to get answer quick without main implementation calling.

        If no sequences, 1 sequence or all sequences are equal then return 0.
        If any sequence are empty then return maximum.
        And in finish try to get external answer.
        """
        if not sequences:
            return 0
        if len(sequences) == 1:
            return 0
        if self._ident(*sequences):
            return 0
        if not all(sequences):
            return self.maximum(*sequences)
        # try get answer from external libs
        return self.external_answer(*sequences)

    @staticmethod
    def _ident(*elements) -> bool:
        """Return True if all sequences are equal.
        """
        try:
            # for hashable elements
            return len(set(elements)) == 1
        except TypeError:
            # for unhashable elements
            for e1, e2 in zip(elements, elements[1:]):
                if e1 != e2:
                    return False
            return True

    def _get_sequences(self, *sequences) -> list:
        """Prepare sequences.

        qval=None: split text by words
        qval=1: do not split sequences. For text this is mean comparing by letters.
        qval>1: split sequences by q-grams
        """
        # by words
        if not self.qval:
            return [s.split() for s in sequences]
        # by chars
        if self.qval == 1:
            return list(sequences)
        # by n-grams
        return [find_ngrams(s, self.qval) for s in sequences]

    def _get_counters(self, *sequences) -> list[Counter]:
        """Prepare sequences and convert it to Counters.
        """
        # already Counters
        if all(isinstance(s, Counter) for s in sequences):
            return list(sequences)
        return [Counter(s) for s in self._get_sequences(*sequences)]

    def _intersect_counters(self, *sequences: Counter) -> Counter:
        intersection = sequences[0].copy()
        for s in sequences[1:]:
            intersection &= s
        return intersection

    def _union_counters(self, *sequences: Counter) -> Counter:
        union = sequences[0].copy()
        for s in sequences[1:]:
            union |= s
        return union

    def _sum_counters(self, *sequences: Counter) -> Counter:
        result = sequences[0].copy()
        for s in sequences[1:]:
            result += s
        return result

    def _count_counters(self, counter: Counter) -> float:
        """Return all elements count from Counter
        """
        if getattr(self, 'as_set', False):
            return len(set(counter))
        else:
            return sum(counter.values())

    def __repr__(self) -> str:
        return '{name}({data})'.format(
            name=type(self).__name__,
            data=self.__dict__,
        )


class BaseSimilarity(Base):
    def distance(self, *sequences) -> float:
        return self.maximum(*sequences) - self.similarity(*sequences)

    def similarity(self, *sequences) -> float:
        return self(*sequences)

    def quick_answer(self, *sequences) -> float | None:
        if not sequences:
            return self.maximum(*sequences)
        if len(sequences) == 1:
            return self.maximum(*sequences)
        if self._ident(*sequences):
            return self.maximum(*sequences)
        if not all(sequences):
            return 0
        # try get answer from external libs
        return self.external_answer(*sequences)
