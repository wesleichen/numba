from __future__ import print_function

import itertools
import math
import sys

from numba.compiler import compile_isolated, Flags
from numba import jit, types
import numba.unittest_support as unittest
from numba import testing
from .support import TestCase, MemoryLeakMixin


enable_pyobj_flags = Flags()
enable_pyobj_flags.set("enable_pyobject")

force_pyobj_flags = Flags()
force_pyobj_flags.set("force_pyobject")


def identity_func(l):
    return l

def create_list(x, y, z):
    return [x, y, z]

def create_nested_list(x, y, z, a, b, c):
    return [[x, y, z], [a, b, c]]

def list_comprehension1():
    return sum([x**2 for x in range(10)])

def list_comprehension2():
    return sum([x for x in range(10) if x % 2 == 0])

def list_comprehension3():
    return sum([math.pow(x, 2) for x in range(10)])

def list_comprehension4():
    return sum([x * y for x in range(10) for y in range(10)])

def list_comprehension5():
    return [x * 2 for x in range(10)]

def list_comprehension6():
    return [[x for x in range(y)] for y in range(3)]


def list_constructor(n):
    return list(range(n))

def list_append(n):
    l = []
    l.append(42)
    for i in range(n):
        l.append(i)
    return l

def list_append_heterogenous(n):
    l = []
    l.append(42.0)
    for i in range(n):
        l.append(i)
    return l

def list_extend(n):
    l = []
    l.extend((5, 42))
    l.extend(range(n))
    return l

def list_pop0(n):
    l = list(range(n))
    res = 0
    while len(l) > 0:
        res += len(l) * l.pop()
    return res

def list_pop1(n, i):
    l = list(range(n))
    x = l.pop(i)
    return x, l

def list_len(n):
    l = list(range(n))
    return len(l)

def list_getitem(n):
    l = list(range(n))
    res = 0
    # Positive indices
    for i in range(len(l)):
        res += i * l[i]
    # Negative indices
    for i in range(-len(l), 0):
        res -= i * l[i]
    return res

def list_setitem(n):
    l = list(range(n))
    res = 0
    # Positive indices
    for i in range(len(l)):
        l[i] = i * l[i]
    # Negative indices
    for i in range(-len(l), 0):
        l[i] = i * l[i]
    for i in range(len(l)):
        res += l[i]
    return res

def list_getslice2(n, start, stop):
    l = list(range(n))
    return l[start:stop]

def list_getslice3(n, start, stop, step):
    l = list(range(n))
    return l[start:stop:step]

def list_setslice2(n, n_source, start, stop):
    # Generic setslice with size change
    l = list(range(n))
    v = list(range(100, 100 + n_source))
    l[start:stop] = v
    return l

def list_setslice3(n, start, stop, step):
    l = list(range(n))
    v = l[start:stop:step]
    for i in range(len(v)):
        v[i] += 100
    l[start:stop:step] = v
    return l

def list_setslice3_arbitrary(n, n_src, start, stop, step):
    l = list(range(n))
    l[start:stop:step] = list(range(100, 100 + n_src))
    return l

def list_clear(n):
    l = list(range(n))
    l.clear()
    return l

def list_copy(n):
    l = list(range(n))
    ll = l.copy()
    l.append(42)
    return l, ll

def list_iteration(n):
    l = list(range(n))
    res = 0
    for i, v in enumerate(l):
        res += i * v
    return res

def list_contains(n):
    l = list(range(n))
    return (0 in l, 1 in l, n - 1 in l, n in l)

def list_index(n, v):
    l = list(range(n, 0, -1))
    return l.index(v)

def list_count(n, v):
    l = []
    for x in range(n):
        l.append(x & 3)
    return l.count(v)

def list_reverse(n):
    l = list(range(n))
    l.reverse()
    return l


class TestLists(MemoryLeakMixin, TestCase):

    def test_identity_func(self):
        pyfunc = identity_func
        with self.assertTypingError():
            cr = compile_isolated(pyfunc, (types.Dummy('list'),))
            cfunc = cr.entry_point
            l = range(10)
            self.assertEqual(cfunc(l), pyfunc(l))

    def test_create_list(self):
        pyfunc = create_list
        cr = compile_isolated(pyfunc, (types.int32, types.int32, types.int32))
        cfunc = cr.entry_point
        self.assertEqual(cfunc(1, 2, 3), pyfunc(1, 2, 3))

    def test_create_nested_list(self):
        pyfunc = create_nested_list
        with self.assertTypingError():
            cr = compile_isolated(pyfunc, (types.int32, types.int32, types.int32,
                types.int32, types.int32, types.int32))
            cfunc = cr.entry_point
            self.assertEqual(cfunc(1, 2, 3, 4, 5, 6), pyfunc(1, 2, 3, 4, 5, 6))

    @testing.allow_interpreter_mode
    def test_list_comprehension(self):
        list_tests = [list_comprehension1,
                      list_comprehension2,
                      list_comprehension3,
                      list_comprehension4,
                      list_comprehension5,
                      list_comprehension6]

        for test in list_tests:
            pyfunc = test
            cr = compile_isolated(pyfunc, ())
            cfunc = cr.entry_point
            self.assertEqual(cfunc(), pyfunc())

    def check_unary_with_size(self, pyfunc, precise=True):
        cfunc = jit(nopython=True)(pyfunc)
        # Use various sizes, to stress the allocation algorithm
        for n in [0, 3, 16, 70, 400]:
            eq = self.assertPreciseEqual if precise else self.assertEqual
            eq(cfunc(n), pyfunc(n))

    def test_constructor(self):
        self.check_unary_with_size(list_constructor)

    def test_append(self):
        self.check_unary_with_size(list_append)

    def test_append_heterogenous(self):
        self.check_unary_with_size(list_append_heterogenous, precise=False)

    def test_extend(self):
        self.check_unary_with_size(list_extend)

    def test_pop0(self):
        self.check_unary_with_size(list_pop0)

    def test_pop1(self):
        pyfunc = list_pop1
        cfunc = jit(nopython=True)(pyfunc)
        for n in [5, 40]:
            for i in [0, 1, n - 2, n - 1, -1, -2, -n + 3, -n + 1]:
                expected = pyfunc(n, i)
                self.assertPreciseEqual(cfunc(n, i), expected)

    def test_pop_errors(self):
        # XXX References are leaked when an exception is raised
        self.disable_leak_check()
        cfunc = jit(nopython=True)(list_pop1)
        with self.assertRaises(IndexError) as cm:
            cfunc(0, 5)
        self.assertEqual(str(cm.exception), "pop from empty list")
        with self.assertRaises(IndexError) as cm:
            cfunc(1, 5)
        self.assertEqual(str(cm.exception), "pop index out of range")

    def test_len(self):
        self.check_unary_with_size(list_len)

    def test_getitem(self):
        self.check_unary_with_size(list_getitem)

    def test_setitem(self):
        self.check_unary_with_size(list_setitem)

    def test_getslice2(self):
        pyfunc = list_getslice2
        cfunc = jit(nopython=True)(pyfunc)
        sizes = [5, 40]
        for n in sizes:
            indices = [0, 1, n - 2, -1, -2, -n + 3, -n - 1, -n]
            for start, stop in itertools.product(indices, indices):
                expected = pyfunc(n, start, stop)
                self.assertPreciseEqual(cfunc(n, start, stop), expected)

    def test_setslice2(self):
        pyfunc = list_setslice2
        cfunc = jit(nopython=True)(pyfunc)
        sizes = [5, 40]
        for n, n_src in itertools.product(sizes, sizes):
            indices = [0, 1, n - 2, -1, -2, -n + 3, -n - 1, -n]
            for start, stop in itertools.product(indices, indices):
                expected = pyfunc(n, n_src, start, stop)
                self.assertPreciseEqual(cfunc(n, n_src, start, stop), expected)

    def test_getslice3(self):
        pyfunc = list_getslice3
        cfunc = jit(nopython=True)(pyfunc)
        for n in [10]:
            indices = [0, 1, n - 2, -1, -2, -n + 3, -n - 1, -n]
            steps = [4, 1, -1, 2, -3]
            for start, stop, step in itertools.product(indices, indices, steps):
                expected = pyfunc(n, start, stop, step)
                self.assertPreciseEqual(cfunc(n, start, stop, step), expected)

    def test_setslice3(self):
        pyfunc = list_setslice3
        cfunc = jit(nopython=True)(pyfunc)
        for n in [10]:
            indices = [0, 1, n - 2, -1, -2, -n + 3, -n - 1, -n]
            steps = [4, 1, -1, 2, -3]
            for start, stop, step in itertools.product(indices, indices, steps):
                expected = pyfunc(n, start, stop, step)
                self.assertPreciseEqual(cfunc(n, start, stop, step), expected)

    def test_setslice3_resize(self):
        # XXX References are leaked when an exception is raised
        self.disable_leak_check()
        pyfunc = list_setslice3_arbitrary
        cfunc = jit(nopython=True)(pyfunc)
        # step == 1 => can resize
        cfunc(5, 10, 0, 2, 1)
        # step != 1 => cannot resize
        with self.assertRaises(ValueError) as cm:
            cfunc(5, 100, 0, 3, 2)
        self.assertIn("cannot resize", str(cm.exception))

    def test_invalid_slice(self):
        # XXX References are leaked when an exception is raised
        self.disable_leak_check()
        pyfunc = list_getslice3
        cfunc = jit(nopython=True)(pyfunc)
        with self.assertRaises(ValueError) as cm:
            cfunc(10, 1, 2, 0)
        self.assertEqual(str(cm.exception), "slice step cannot be zero")

    def test_iteration(self):
        self.check_unary_with_size(list_iteration)

    def test_reverse(self):
        self.check_unary_with_size(list_reverse)

    def test_contains(self):
        self.check_unary_with_size(list_contains)

    def test_index(self):
        # XXX References are leaked when an exception is raised
        self.disable_leak_check()
        pyfunc = list_index
        cfunc = jit(nopython=True)(pyfunc)
        for v in (1, 5, 10):
            self.assertPreciseEqual(cfunc(16, v), pyfunc(16, v))
        with self.assertRaises(IndexError):
            cfunc(16, 42)

    def test_count(self):
        pyfunc = list_count
        cfunc = jit(nopython=True)(pyfunc)
        for v in range(5):
            self.assertPreciseEqual(cfunc(18, v), pyfunc(18, v))

    @unittest.skipUnless(sys.version_info >= (3, 3),
                         "list.clear() needs Python 3.3+")
    def test_clear(self):
        self.check_unary_with_size(list_clear)

    @unittest.skipUnless(sys.version_info >= (3, 3),
                         "list.copy() needs Python 3.3+")
    def test_copy(self):
        self.check_unary_with_size(list_copy)


if __name__ == '__main__':
    unittest.main()
