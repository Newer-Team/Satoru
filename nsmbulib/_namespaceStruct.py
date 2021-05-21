import collections
import struct


_DIGITS = '0123456789'

_FORMAT_CHARS_PAD = 'x'
_FORMAT_CHARS_BYTES1 = 'c'
_FORMAT_CHARS_BYTES = 'sp'
_FORMAT_CHARS_INT = 'bBhHiIlLqQ'
_FORMAT_CHARS_FLOAT = 'fd'
_FORMAT_CHARS_BOOL = '?'
_FORMAT_CHARS = (_FORMAT_CHARS_PAD + _FORMAT_CHARS_BYTES1
                 + _FORMAT_CHARS_BYTES + _FORMAT_CHARS_INT
                 + _FORMAT_CHARS_FLOAT + _FORMAT_CHARS_BOOL)


def _isStructMember(name, value):
    """
    Determine whether an attribute with this name and value represents a
    struct member or not.
    """
    # Determine whether this is a struct item or not

    if name.startswith('__') and name.endswith('__'):
        return False

    if not isinstance(value, str) or len(value) < 1:
        return False

    # See if it's strictly zero or more digits followed by one format
    # char or one format char repeated multiple times
    if value[0] in _DIGITS:
        if value[-1] not in _FORMAT_CHARS:
            return False
        if not all(c in _DIGITS for c in value[:-1]):
            return False
    else:
        if value[0] not in _FORMAT_CHARS:
            return False
        if not all(c == value[0] for c in value):
            return False
        if len(value) > 1:
            value = str(len(value)) + value[0]

    return value


def _initializeValueForSingleFormat(format):
    """
    Return a decent default value for this format. (Don't include count
    prefixes in the format.)
    """
    if format in _FORMAT_CHARS_BYTES1 + _FORMAT_CHARS_BYTES:
        return b'\0'
    elif format in _FORMAT_CHARS_INT:
        return 0
    elif format in _FORMAT_CHARS_FLOAT:
        return 0.0
    elif format in _FORMAT_CHARS_BOOL:
        return False


def _initializeValueForFormat(format):
    """
    Return a decent default value for this format.
    """
    if format[0] not in _DIGITS:
        return _initializeValueForSingleFormat(format)

    count = int(format[:-1])

    # Handle the bytes case separately, because the preceding number
    # there has a different meaning
    if format[-1] in _FORMAT_CHARS_BYTES:
        return b'\0' * count

    return [_initializeValueForSingleFormat(format[-1])] * count


def _validateSingleValue(format, value):
    """
    Is this a valid value for this format?
    """

    # Special-case bytes first, because they might have a length prefix
    if len(format) > 1 and format[-1] in _FORMAT_CHARS_BYTES:
        return isinstance(value, bytes) and len(value) == int(format[:-1])

    if format in _FORMAT_CHARS_BYTES1:
        return isinstance(value, bytes) and len(value) == 1

    if format in _FORMAT_CHARS_BOOL:
        return value in (True, False)

    if format in _FORMAT_CHARS_FLOAT:
        return isinstance(value, (int, float))

    if format in _FORMAT_CHARS_INT:
        # Now to validate all the int sizes :/
        min_, max_ = {
            'b': (-0x80, 0x7F),
            'B': (0, 0xFF),
            'h': (-0x8000, 0x7FFF),
            'H': (0, 0xFFFF),
            'i': (-0x80000000, 0x7FFFFFFF),
            'I': (0, 0xFFFFFFFF),
            'l': (-0x80000000, 0x7FFFFFFF),
            'L': (0, 0xFFFFFFFF),
            'q': (-0x8000000000000000, 0x7FFFFFFFFFFFFFFF),
            'Q': (0, 0xFFFFFFFFFFFFFFFF),
        }[format]

        return isinstance(value, int) and min_ <= value <= max_

    raise ValueError("Shouldn't have reached this line. Parameters: '%s', %s'"
                     % (str(format), str(value)))


class _NamespaceStructInitialNamespace:
    """
    This is a temporary namespace for NamespaceStruct's (and subclasses
    thereof) when they are being evaluated for the first time.
    It behaves like a dictionary, but categorizes each attribute as
    either a struct item or something else.
    """
    def __init__(self):
        super().__init__()
        self.structMembers = collections.OrderedDict()
        self.other = {}

    def __setitem__(self, key, val):
        # Put it into the proper dict depending on if it's a struct
        # member or not
        newVal = _isStructMember(key, val)
        if newVal:
            self.structMembers[key] = newVal
        else:
            self.other[key] = val

    def __getitem__(self, key):
        if key in self.other:
            return self.other[key]
        else:
            raise KeyError


class _NamespaceStructMeta(type):
    """
    Metaclass for the NamespaceStruct class.
    Huge thanks to Jake Vanderplas for his great guide on how Python
    metaclasses work:
    https://jakevdp.github.io/blog/2012/12/01/a-primer-on-python-metaclasses/
    I also used the built-in enum module and PEP 3115 as references.
    """

    @classmethod
    def __prepare__(cls, name, bases):
        """
        Return an object to be used as the namespace of a
        NamespaceStruct while it is being evaluated.
        """
        return _NamespaceStructInitialNamespace()

    def __new__(cls, name, parents, initNamespace):
        """
        Create a new NamespaceStruct.
        """
        structMembers = initNamespace.structMembers
        namespace = initNamespace.other

        namespace['_structMembers'] = structMembers

        # Set initial values for the struct members
        for name, format in structMembers.items():
            namespace[name] = _initializeValueForFormat(format)

        return super(_NamespaceStructMeta, cls).__new__(cls, name, parents,
                                                        namespace)

    @property
    def formatStr(cls):
        """
        Return the format string representing the structure
        """
        return cls.ENDIAN + ''.join(cls._structMembers.values())


class NamespaceStruct(metaclass=_NamespaceStructMeta):
    """
    You can subclass this to set up your own sort-of-C-style namespace
    that is also a struct!
    """
    _structMembers = None

    ENDIAN = '>' # It's perfectly acceptable to modify this in
                 # subclasses

    def __init__(self, initialValues=None):
        """
        Initialize the NamespaceStruct, optionally with a dict defining
        initial values for some or all members.
        """
        if initialValues is not None:
            for name, value in initialValues.items():
                setattr(self, name, value)

    @property
    def formatStr(self):
        return type(self).formatStr

    @classmethod
    def loadFrom(cls, data, offset=0):
        """
        Create a NamespaceStruct instance with values loaded from
        `data`, starting at `offset`. (Think `struct.unpack()`.)
        """
        values = struct.unpack_from(cls.formatStr, data, offset)

        namedValues = {}
        i = 0
        for name, format in cls._structMembers.items():
            if format[-1] in _FORMAT_CHARS_PAD:
                continue
            elif len(format) == 1 or format[-1] in _FORMAT_CHARS_BYTES:
                namedValues[name] = values[i]
                i += 1
            else:
                newList = []
                for j in range(int(format[:-1])):
                    newList.append(values[i])
                    i += 1
                namedValues[name] = newList

        obj = cls(namedValues)

        return obj

    def save(self):
        """
        Convert the values in this struct to a bytes object. (Think
        `struct.pack()`.)
        """
        allValues = []
        for name, format in self._structMembers.items():
            if format[-1] in _FORMAT_CHARS_PAD:
                continue
            val = getattr(self, name)
            try:
                for item in val:
                    allValues.append(item)
            except TypeError:
                allValues.append(val)
        return struct.pack(self.formatStr, *allValues)

    @property
    def structSize(self):
        """
        Return the length of this struct, in bytes.
        """
        return struct.calcsize(self.formatStr)

    def __setattr__(self, key, value):
        """
        Validate all values put into the struct.
        """
        format = self._structMembers.get(key)
        if format is not None:
            # Validate it!
            if len(format) == 1 or format[-1] in _FORMAT_CHARS_BYTES:
                isValid = _validateSingleValue(format, value)
            elif len(value) != int(format[:-1]):
                isValid == False
            else:
                isValid = True
                for item in value:
                    isValid &= _validateSingleValue(format[-1], item)
            if not isValid:
                raise ValueError('%s is not a valid value for the format "%s"'
                                 % (str(value), format))
        super().__setattr__(key, value)
