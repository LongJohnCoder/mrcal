#!/usr/bin/python3

import sys
import numpy as np
import numpysane as nps
import os
import re
from inspect import currentframe

Nchecks = 0
NchecksFailed = 0

# no line breaks. Useful for test reporting. Yes, this sets global state, but
# we're running a test harness. This is fine
np.set_printoptions(linewidth=1e10, suppress=True)


def test_location():
    r'''Reports string describing current location in the test'''


    filename_this = os.path.split( __file__ )[1]

    frame = currentframe().f_back.f_back

    # I keep popping the stack until I leave the testutils file and I'm not in a
    # function called "check"
    while frame:
        if frame.f_back is None or \
           (not frame.f_code.co_filename.endswith(filename_this) and
            frame.f_code.co_name != "check" ):
            break
        frame = frame.f_back

    testfile = os.path.split(frame.f_code.co_filename)[1]
    try:
        return "{}:{}".format(testfile, frame.f_lineno)
    except:
        return ''


def print_red(x):
    """print the message in red"""
    sys.stdout.write("\x1b[31m" + test_location() + ": " + x + "\x1b[0m\n")


def print_green(x):
    """Print the message in green"""
    sys.stdout.write("\x1b[32m" + test_location() + ": " + x + "\x1b[0m\n")


def relative_scale(a,b, eps = 1e-6):
    return (np.abs(a) + np.abs(b)) / 2 + eps

def relative_diff(a,b, eps = 1e-6):
    return (a - b) / relative_scale(a,b, eps)

def confirm_equal(x, xref, msg='', eps=1e-6,
                  relative=False,
                  worstcase=False,
                  percentile=None):
    r'''If x is equal to xref, report test success.

    msg identifies this check. eps sets the RMS equality tolerance. The x,xref
    arguments can be given as many different types. This function tries to do
    the right thing.

    if relative: I look at a relative error:
                 err = (a-b) / ((abs(a)+abs(b))/2 + eps)
    else:        I look at absolute error:
                 err = a-b

    if worstcase: I look at the worst-case error
                  error = np.max(np.abs(err))
    elif percentile is not None: I look at the given point in the error distribution
                  error = np.percentile(np.abs(err), percentile)
    else:         RMS error
                  error = np.sqrt(nps.norm2(err) / len(err))
    '''

    global Nchecks
    global NchecksFailed
    Nchecks = Nchecks + 1

    # strip all trailing whitespace in each line, in case these are strings
    if isinstance(x, str):
        x = re.sub('[ \t]+(\n|$)', '\\1', x)
    if isinstance(xref, str):
        xref = re.sub('[ \t]+(\n|$)', '\\1', xref)

    # convert data to numpy if possible
    try:
        xref = np.array(xref)
    except:
        pass
    try:
        x = np.array(x)
    except:
        pass

    try:  # flatten array if possible
        x = x.ravel()
        xref = xref.ravel()
    except:
        pass

    try:
        N = x.shape[0]
    except:
        N = 1
    try:
        Nref = xref.shape[0]
    except:
        Nref = 1

    if N != Nref:

        # Comparing an array to a scalar reference is allowed
        if Nref == 1:
            xref = np.ones((N,), dtype=float) * xref
            Nref = N
        else:
            print_red(("FAILED{}: mismatched array sizes: N = {} but Nref = {}. Arrays: \n" +
                       "x = {}\n" +
                       "xref = {}").
                      format((': ' + msg) if msg else '',
                             N, Nref,
                             x, xref))
            NchecksFailed = NchecksFailed + 1
            return False

    if N != 0:
        try:  # I I can subtract, get the error that way
            if relative:
                diff = relative_diff(x, xref)
            else:
                diff = x - xref

            if worstcase:
                what = 'worst-case'
                err  = np.max(np.abs(diff))
            elif percentile is not None:
                what = f'{percentile}%-percentile'
                err  = np.percentile(np.abs(diff), percentile, interpolation='higher')
            else:
                what = 'RMS'
                err  = np.sqrt(nps.norm2(diff) / len(diff))

            if not np.all(np.isfinite(err)):
                print_red(f"FAILED{(': ' + msg) if msg else ''}: Some comparison results are NaN or Inf. {what}. error_x_xref =\n{nps.cat(err,x,xref)}")
                NchecksFailed = NchecksFailed + 1
                return False
            if err > eps:
                print_red(f"FAILED{(': ' + msg) if msg else ''}: {what} error = {err}. x_xref_err =\n{nps.cat(x,xref,diff)}")
                NchecksFailed = NchecksFailed + 1
                return False
        except:  # Can't subtract. Do == instead
            if not np.array_equal(x, xref):
                print_red(f"FAILED{(': ' + msg) if msg else ''}: x_xref =\n{nps.cat(x,xref)}")
                NchecksFailed = NchecksFailed + 1
                return False
    print_green("OK" + (': ' + msg) if msg else '')
    return True


def confirm(x, msg=''):
    r'''If x is true, report test success.

    msg identifies this check'''

    global Nchecks
    global NchecksFailed
    Nchecks = Nchecks + 1

    if not x:
        print_red("FAILED{}".format((': ' + msg) if msg else ''))
        NchecksFailed = NchecksFailed + 1
        return False
    print_green("OK{}".format((': ' + msg) if msg else ''))
    return True


def finish():
    r'''Finalize the executed tests.

    Prints the test summary. Exits successfully iff all the tests passed.

    '''
    if not Nchecks and not NchecksFailed:
        print_red("No tests defined")
        sys.exit(0)

    if NchecksFailed:
        print_red("Some tests failed: {} out of {}".format(NchecksFailed, Nchecks))
        sys.exit(1)

    print_green("All tests passed: {} total".format(Nchecks))
    sys.exit(0)
