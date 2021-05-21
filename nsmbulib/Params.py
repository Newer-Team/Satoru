
import collections


class InvalidParamsError(ValueError):
    """
    The params file is invalid.
    """


def load(data):
    """
    Convert a string containing .params data to a dict containing
    equivalent Python values.

    Raises InvalidParamsError if the data is not a valid .params file.
    """

    # A .params file is essentially a set of nested dictionaries.
    #
    # In general, what can make parsing parameter files confusing is
    # that a single set of delimiters ("{" and "}") has two very
    # different meanings depending on context. They can be used to
    # contain a dictionary, or to contain a dictionary entry.
    #
    # Thus, "{" alternates meanings at each level of nesting:
    # dictionary, entry, dictionary, entry, ...

    # Break the filedata string into lines, and remove indentation and
    # trailing whitespace. The other parser functions assume that this
    # has already been done.
    lines = [line.strip() for line in data.split('\n')]
    lines = [L for L in lines if len(L) > 0 and not L.startswith('#')]

    # Sanity check
    if lines[0] != '{':
        raise InvalidParamsError("This doesn't seem to be a .params file.")

    # The entire parameters file is just a dictionary. Parse it and
    # return it. (We can discard any leftover data; there shouldn't be
    # any.)
    try:
        return _loadDict(lines)[0]
    except Exception as e:
        raise InvalidParamsError('There was an error parsing the .params file.'
            ) from e


def _loadDict(lines):
    """
    Parse a dictionary:
    {
        {
            key
            value
        }
        {
            key
            value
        }
    }
    (Extra data here, after the end of the dictionary, is allowed.)

    The first two lines must both be '{'.
    Returns: the assembled dictionary, and whatever file data is left
    over afterward (or [] if there is none).
    """

    # Sanity checks, and remove the leading '{'
    assert lines[0] == '{' and lines[1] == '{'
    lines = lines[1:]

    # This is the dictionary we'll be building
    retdict = collections.OrderedDict()

    # Keep going until we hit the end of the list.
    while len(lines) > 0 and lines[0] != '}':

        # Parse this entry, and keep whatever file data is left over
        key, val, lines = _loadEntry(lines)

        # Add it to the dictionary we're building
        retdict[key] = val

    # Oh, we're done! We hit the end of the dictionary. Return it
    # along with whatever we didn't parse (excluding the final '}').
    return retdict, lines[1:]


def _loadEntry(lines):
    """
    Parse a dictionary key/val pair:
    {
        key (atomic)
        value (could be an atomic or a dict)
    }
    Must begin with a '{'.
    Returns: the key, the value, and the rest of the file data
    afterward.
    """
    # Sanity checks, and remove the leading '{'
    assert lines[0] == '{' and lines[1] != '{'
    lines = lines[1:]

    # The key cannot be a dict. Parse and remove it.
    key = _loadAtomic(lines[0])
    lines = lines[1:]

    # The value might be a dict, though. Parase and it, too.
    if lines[0] == '{':
        value, lines = _loadDict(lines)
    else:
        value = _loadAtomic(lines[0])
        lines = lines[1:]

    # Ensure that we end with a }, and remove that, too.
    assert lines[0] == '}'
    lines = lines[1:]

    # Return the key, value, and file data sans this entire key/value
    # pair.
    return key, value, lines


def _loadAtomic(line):
    """
    Parse an atomic parameter into a value.
    There are four types of atomic parameters:
    - integer (preceded by "-" if negative)
    - float (same as above)
    - string (delimited by '"'s)
    - list (a ' '-separated list of other atomics)
    """
    # This EAFP approach is nice and bulletproof.

    try:
        # It's an int!
        return int(line)
    except ValueError:
        try:
            # No, it's a float!
            return float(line)
        except ValueError:
            # No, it must be a string or tuple.
            if line.count('"') == 2 and line[0] + line[-1] == '""':
                # It's a string.
                return line[1:-1]
            else:
                # Must be a tuple!

                retval = []
                for val in line.split(' '):
                    # Yes, this does fix crashes
                    # (Splatoon/Enm_TakolienSpeedUp.params)
                    if val == '': continue
                    retval.append(_loadAtomic(val))
                return tuple(retval)


def save(contents, minify=False):
    """
    Convert a dict containing various Python values to a string in the
    format of a .params file.

    If `minify` is `True`, the .params file will be minified as much as
    possible. If `minify` is `False`, the formatting will match that of
    retail .params files as closely as possible, including various
    oddities such as inexplicable blank lines and trailing spaces.
    """

    output = _saveDict(contents, 0, minify)

    # We need to remove one of the trailing \n's, hence the [:-1].
    return output if minify else output[:-1]


def _saveDict(dictdata, indent, minify):
    """
    Render a parameters dictionary.
    """
    if minify:
        first = '{\n'
        last = '}\n'
    else:
        first = '\t' * indent + '{\n'
        last = '\t' * indent + '}\n\n' # Yes, there is a stray \n there.

    middle = ''
    for key, value in dictdata.items():
        middle += _saveEntry(key, value, indent + 1, minify)

    return first + middle + last


def _saveEntry(key, value, indent, minify):
    """
    Render a parameters dictionary entry.
    """
    if minify:
        first = '{\n'
        last = '}\n'
    else:
        first = '\t' * indent + '{\n'
        last = '\t' * indent + '}\n'

    keystr = _saveAtomicLine(key, indent + 1, minify)
    if isinstance(value, dict):
        valstr = _saveDict(value, indent + 1, minify)
    else:
        valstr = _saveAtomicLine(value, indent + 1, minify)

    return first + keystr + valstr + last


def _saveAtomicLine(value, indent, minify):
    """
    Render a parameters atomic value as a string representing the entire
    line at the indentation level given.
    """
    if minify:
        first = ''
        last = '\n'
    else:
        first = '\t' * indent
        last = ' \n' # Yes, that space is supposed to be there.
    return first + _saveAtomic(value) + last


def _saveAtomic(value):
    """
    Render a parameters atomic value as a string
    """
    if isinstance(value, str):
        return '"' + value + '"'
    elif isinstance(value, float):
        return '%.8F' % value # force exactly 8 decimal places
    elif isinstance(value, list) or isinstance(value, tuple):
        return ' '.join(_saveAtomic(item) for item in value)
    else:
        return str(value)
