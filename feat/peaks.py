from __future__ import print_function
import numpy as np


def peak_bounds(x, i):
    """ Find bounds around peak

    Parameters
    ----------

    x: np.ndarray
        Array of values
    i: int
        Index location of a peak

    >>> #                  bound    Peak     bound
    >>> #                  |        |        |
    >>> peak_bounds([3, 2, 1, 2, 3, 4, 3, 2, 1, 2, 3], 5)
    (2, 8)

    >>> peak_bounds([3, 1, 2, 3, 4], 4)
    (1, 4)
    """
    smallest = x[i]
    j = i
    while j + 1< len(x) and x[j] >= x[j + 1]:
        j += 1

    k = i
    while k - 1 >= 0 and x[k] >= x[k - 1]:
        k -= 1

    return k, j


def inactive_regions(x, k, abs_tol=0):
    """ Seek periods of length k that of small deviation

    Examples
    --------

    >>> inactive_regions([1, 1, 2, 3, 3, 3, 3, 3, 4, 5, 5, 6], 2)
    [(1, slice(0, 2)), (3, slice(3, 8)), (5, slice(9, 11))]
    """
    start = 0
    result = []
    for i in range(len(x)):
        if abs(x[i] - x[start]) > abs_tol:  # End of chain
            if (i - start) >= k:
                result.append((x[start], slice(start, i)))
            start = i
    return result


def seek_inactive(x, start, length, direction=-1, abstol=0):
    """ Seek inactive region to the left of start

    Example
    -------

    >>> #                    _______        |
    >>> seek_inactive([3, 2, 1, 1, 1, 2, 3, 4, 2], start=7, length=3)
    (1, slice(2, 4))

    When no sufficiently long sequence is found we return the end

    >>> #              _                    |
    >>> seek_inactive([3, 2, 1, 1, 1, 2, 3, 4, 2], start=7, length=5)
    (3, slice(0, 0))
    """
    end = -1 if direction == -1 else len(x)
    ind = start
    for i in range(start, end, direction):
        if abs(x[i] - x[ind]) > abstol:
            ind = i
        if abs(ind - i) >= length - 1:
            return x[ind], slice(ind, i, direction)
    if direction == 1:
        return x[-1], slice(-1, -1)
    else:
        return x[0], slice(0, 0)


def many_peaks(n, x):
    """ Find bounds around the n largest maxima

    >>> #              |____________  ___|______
    >>> many_peaks(2, [5, 3, 1, 1, 1, 2, 3, 2, 1, 2, 2])  # doctest: +NORMALIZE_WHITESPACE
    [{'start': 0, 'stop': 4, 'location': 0, 'value': 5.0},
     {'start': 5, 'stop': 8, 'location': 6, 'value': 3.0}]

    """
    x = np.array(x, dtype='f8')

    results = []
    for i in range(n):
        loc = np.nanargmax(x)
        value = x[loc]
        start, stop = peak_bounds(x, loc)
        x[start: stop+1] = np.nan

        results.append({'location': loc, 'value': value,
                        'start': start, 'stop': stop})
    return results

if __name__ == '__main__':
    import pandas as pd
    df = pd.read_csv('data/igpk.csv')
    x = df.Close.values
    print (many_peaks(5, x))
