# Thanks to Kinnay for setting this up

import ctypes
import os.path
import struct
import sys


lib = None
def getLib():
    """
    Get the DLL library. Reuse the existing instance if it's
    already loaded.
    """
    global lib
    if lib is None:
        architecture = 64 if sys.maxsize > 2**32 else 32

        libPath = os.path.join(os.path.dirname(__file__), '_cAlgorithms%d.dll' % architecture)
        lib = ctypes.CDLL(libPath)

        # http://stackoverflow.com/a/32331948/4718769
        lib.decodeRGBA8.restype = ctypes.POINTER(ctypes.c_char)
        lib.decodeDXT5.restype = ctypes.POINTER(ctypes.c_char)
        lib.decompress.restype = ctypes.POINTER(ctypes.c_char)
        lib.compress.restype = ctypes.POINTER(ctypes.c_char)
    return lib


def decodeRGBA8(w, h, data):
    lib = getLib()
    return ctypes.string_at(lib.decodeRGBA8(w, h, data), w * h * 4)

def decodeBC3(w, h, data):
    lib = getLib()
    # #raise Exception
    # happy = ctypes.string_at(lib.decodeDXT5(w, h, data), w * h * 4)
    # from PyQt5 import QtGui, QtWidgets, QtCore
    # happy2 = bytearray(len(happy))
    # print('made happy 2')
    # for i in range(len(happy) // 4):
    #     i *= 4
    #     happy2[i+0] = happy[i+2]
    #     happy2[i+1] = happy[i+1]
    #     happy2[i+2] = happy[i+0]
    #     happy2[i+3] = happy[i+3]
    # print('put together happy 2')
    # import PIL
    # i = PIL.Image.frombytes('RGBA', (2048, 512), bytes(happy2))
    # print('made image obj')
    # #i = QtGui.QImage(bytes(happy2), 2048, 512, 2048*4, QtGui.QImage.Format_ARGB32)
    # i.save('DXT5qt %s.png'
    #     % str(__import__('random').random()))
    # print('I saved the image!')
    raise Exception # This still doesn't work.
    # ALSO, it needs to also return the intermediate deswizzled form.
    return ctypes.string_at(lib.decodeBC3(w, h, data), w * h * 4)

def decompressYaz0(data):
    lib = getLib()
    size = struct.unpack_from('>I', data, 4)[0]
    return ctypes.string_at(lib.decompress(data), size)

def compressYaz0(data):
    lib = getLib()
    size = len(data)
    out = struct.pack('>4sIII', 'Yaz0', size, 0, 0)
    out += ctypes.string_at(lib.compress(data, size), size + (size + 8) // 8)
    return out


