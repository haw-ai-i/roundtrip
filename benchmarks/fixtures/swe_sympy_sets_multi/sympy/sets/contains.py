from sympy.core import S
from sympy.logic.boolalg import BooleanFunction

class Contains(BooleanFunction):
    """
    Asserts that x is an element of set S.

    Examples
    ========

    >>> from sympy import Symbol, Integer, S
    >>> from sympy.sets.contains import Contains
    >>> from sympy.sets.sets import Interval
    >>> x = Symbol('x')
    >>> Contains(x, Interval(0, 1))
    Contains(x, Interval(0, 1))
    >>> Contains(Integer(1), Interval(0, 2))
    True
    """

    @classmethod
    def eval(cls, x, s):
        from sympy.sets.sets import Set
        if not isinstance(s, Set):
            raise TypeError(f"expecting Set, not {type(s).__name__}")

        res = s.contains(x)
        if not isinstance(res, Contains) and (res in (S.true, S.false) or isinstance(res, Set)):
            return res
        return None

    @property
    def binary_symbols(self):
        from sympy.core.relational import Eq, Ne
        s = self.args[1]
        binary_syms = set()
        for i in s.args:
            is_bool = getattr(i, 'is_Boolean', False)
            is_sym = getattr(i, 'is_Symbol', False)
            is_eq_ne = isinstance(i, (Eq, Ne))
            if is_bool or is_sym or is_eq_ne:
                binary_syms.update(i.binary_symbols)
        return binary_syms

    def as_set(self):
        return self.args[1]