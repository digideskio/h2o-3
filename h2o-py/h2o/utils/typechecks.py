# -*- encoding: utf-8 -*-
"""
Utilities for checking types of variables.

:copyright: (c) 2016 H2O.ai
:license:   Apache License Version 2.0 (see LICENSE for details)
"""
from __future__ import absolute_import, division, print_function, unicode_literals

import re
import sys
import tokenize

from h2o.utils.compatibility import *  # NOQA
from h2o.exceptions import H2OTypeError, H2OValueError

__all__ = ("is_str", "is_int", "is_numeric", "is_listlike",
           "assert_is_type", "assert_matches", "assert_satisfies",
           "assert_is_bool", "assert_is_int", "assert_is_numeric", "assert_is_str",
           "assert_maybe_int", "assert_maybe_numeric", "assert_maybe_str")


if PY2:
    # noinspection PyProtectedMember
    from h2o.utils.compatibility import _native_unicode, _native_long
    _str_type = (str, _native_unicode)
    _int_type = (int, _native_long)
    _num_type = (int, _native_long, float)
else:
    _str_type = str
    _int_type = int
    _num_type = (int, float)




def is_str(s):
    """Test whether the provided argument is a string."""
    return isinstance(s, _str_type)


def is_int(i):
    """Test whether the provided argument is an integer."""
    return isinstance(i, _int_type)


def is_numeric(x):
    """Test whether the provided argument is either an integer or a float."""
    return isinstance(x, _num_type)


def is_listlike(s):
    """Return True if s is either a list or a tuple."""
    return isinstance(s, (list, tuple))



def assert_is_type(var, expected_type, message=None, skip_frames=1):
    """
    Assert that the argument has the specified type.

    This function is used to check that the type of the argument is correct, otherwises it raises an error.
    Use it like following::

        assert_is_type(fr, H2OFrame)
        assert_is_type(port, (int, str))

    :param var: variable to check.
    :param expected_type: the expected type. This could be either a raw type (such as ``bool``), a ``None`` literal,
        a class name, or a tuple of those. If ``str`` or ``int`` are passed, then on Py2 we will also attempt to
        match ``unicode`` and ``long`` respectively (so that the check is Py2/Py3 compatible).
    :param message: override the error message.
    :param skip_frames: how many local frames to skip when printing out the error.

    :raises H2OTypeError: if the argument is not of the desired type.
    """
    if _check_type(var, expected_type): return
    vname = _retrieve_assert_arguments()[0]
    raise H2OTypeError(var_name=vname, var_value=var, exp_type=expected_type, message=message,
                       skip_frames=skip_frames)



def assert_is_none(s):
    """Assert that the argument is None."""
    assert_is_type(s, None, skip_frames=2)

def assert_is_str(s):
    """Assert that the argument is a string."""
    assert_is_type(s, str, skip_frames=2)

def assert_maybe_str(s):
    """Assert that the argument is a string or None."""
    assert_is_type(s, (str, None), skip_frames=2)

def assert_is_int(x):
    """Assert that the argument is integer."""
    assert_is_type(x, int, skip_frames=2)

def assert_maybe_int(x):
    """Assert that the argument is integer or None."""
    assert_is_type(x, (int, None), skip_frames=2)

def assert_is_bool(b):
    """Assert that the argument is boolean."""
    assert_is_type(b, bool, skip_frames=2)

def assert_is_numeric(x):
    """Assert that the argument is numeric (integer or float)."""
    assert_is_type(x, (int, float), skip_frames=2)

def assert_maybe_numeric(x):
    """Assert that the argument is either numeric or None."""
    assert_is_type(x, (int, float, None), skip_frames=2)


def assert_true(cond, message):
    """Same as traditional assert, only raises H2OValueError instead."""
    if not cond:
        raise H2OValueError(message)


def assert_matches(v, regex):
    """
    Assert that string variable matches the provided regular expression.

    :param v: variable to check.
    :param regex: regular expression to check against (can be either a string, or compiled regexp).
    """
    m = re.match(regex, v)
    if m is None:
        vn = _retrieve_assert_arguments()[0]
        message = "Argument `{var}` (= {val!r}) did not match /{regex}/".format(var=vn, regex=regex, val=v)
        raise H2OValueError(message, var_name=vn, skip_frames=1)
    return m


def assert_satisfies(v, cond):
    """
    Assert that variable satisfies the provided condition.

    :param v: variable to check. Its value is only used for error reporting.
    :param bool cond: condition that must be satisfied. Should be somehow related to the variable ``v``.
    """
    if not cond:
        vname, vexpr = _retrieve_assert_arguments()
        raise H2OValueError("Argument `{var}` (= {val!r}) does not satisfy the condition {expr}"
                            .format(var=vname, val=v, expr=vexpr), var_name=vname, skip_frames=1)


def _retrieve_assert_arguments():
    """
    Magic variable name retrieval.

    This function is designed as a helper for assert_*() functions. Typically such assertion is used like this::

        assert_is_type(num_threads, int)

    If the variable `num_threads` turns out to be non-integer, we would like to raise an exception such as

        H2OTypeError("`num_threads` is expected to be integer, but got <str>")

    and in order to compose an error message like that, we need to know that the variables that was passed to
    assert_is_type() carries a name "num_threads". Naturally, the variable itself knows nothing about that.

    This is where this function comes in: we walk up the stack trace until the first frame outside of this
    file, find the original line that called the assert_is_int() function, and extract the variable name from
    that line. This is slightly fragile, in particular we assume that only one assert_* statement can be per line,
    or that this statement does not spill over multiple lines, or that the argument is not a complicated
    expression like `assert_is_int(foo(x))` or `assert_is_str(x[1,2])`. I do not foresee such complexities in the
    code, but if they arise this function can be amended to parse those cases properly.
    """
    try:
        raise RuntimeError("Catch me!")
    except RuntimeError:
        # Walk up the stacktrace until we are outside of this file
        tb = sys.exc_info()[2]
        assert tb.tb_frame.f_code.co_name == "_retrieve_assert_arguments"
        this_filename = tb.tb_frame.f_code.co_filename
        fr = tb.tb_frame
        while fr is not None and fr.f_code.co_filename == this_filename:
            fr = fr.f_back

        # Read the source file and tokenize it, extracting the expressions.
        with open(fr.f_code.co_filename, "r") as f:
            # Skip initial lines that are irrelevant
            for i in range(fr.f_lineno - 1): next(f)
            # Create tokenizer
            g = tokenize.generate_tokens(f.readline)
            step = 0
            args_tokens = []
            level = 0
            for ttt in g:
                if step == 0:
                    if ttt[0] != tokenize.NAME: continue
                    if not ttt[1].startswith("assert_"): continue
                    step = 1
                elif step == 1:
                    assert ttt[0] == tokenize.OP and ttt[1] == "("
                    args_tokens.append([])
                    step = 2
                elif step == 2:
                    if level == 0 and ttt[0] == tokenize.OP and ttt[1] == ",":
                        args_tokens.append([])
                    elif level == 0 and ttt[0] == tokenize.OP and ttt[1] == ")":
                        break
                    else:
                        if ttt[0] == tokenize.OP and ttt[1] in "([{": level += 1
                        if ttt[0] == tokenize.OP and ttt[1] in ")]}": level -= 1
                        assert level >= 0, "Parse error: parentheses level became negative"
                        args_tokens[-1].append(ttt)
            args = [tokenize.untokenize(at).strip().replace("\n", " ") for at in args_tokens]
            return args




def _check_type(s, stype, _nested=False):
    """
    Return True if the variable has the specified type, and False otherwise.

    :param s: variable to check.
    :param stype: expected type (should be either a type, a tuple of types, or None).
    """
    if stype is None:
        return s is None
    elif stype is str:
        return isinstance(s, _str_type)
    elif stype is int:
        return isinstance(s, _int_type)
    elif isinstance(stype, type):
        return isinstance(s, stype)
    elif isinstance(stype, tuple) and not _nested:
        return any(_check_type(s, tt, _nested=True) for tt in stype)
    else:
        raise RuntimeError("Ivalid argument %r to _check_type()" % stype)
