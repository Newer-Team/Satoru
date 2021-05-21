import os
import shutil
import subprocess

from . import _common



def decompress(data):
    """
    Decompress Yaz0 using YAZ0UNP
    """

    # YAZ0UNP usage instructions:
    # 1) Call "YAZ0UNP.EXE compressedFile"
    # 2) The uncompressed data is put into UNPACK/0.UNP

    if data.startswith(b'Yaz0\0\0\0\0') and len(data) >= 16:
        # This is a valid Yaz0 file of zero length, which YAZ0UNP would
        # choke on. Just return b'' manually.
        return b''

    with _common.cwdAsPathTo(__file__):

        with open(_common.TEMP_FILE_NAME + '.szs', 'wb') as f:
            f.write(data)

        with _common.getDevNull() as devnull:
            with subprocess.Popen(
                ['YAZ0UNP.EXE', _common.TEMP_FILE_NAME + '.szs'],
                stdout=devnull,
                ) as proc:
                proc.communicate()

        os.remove(_common.TEMP_FILE_NAME + '.szs')

        with open('UNPACK/0.UNP', 'rb') as f:
            unp = f.read()

        shutil.rmtree('UNPACK')

    return unp


def compress(data, compressionLevel):
    """
    Compress Yaz0 somehow
    """
    if compressionLevel == 0:
        return _compressFake(data)
    else:
        return _compressYAZ0COMP(data)


def _compressFake(data):
    """
    Run this data through fake_yaz0
    """

    # fake_yaz0 usage instructions:
    # 1) Call "fake_yaz0.exe uncompressedFile outputFile"
    # 2) The "compressed" data is put into outputFile.

    with _common.cwdAsPathTo(__file__):

        with open(_common.TEMP_FILE_NAME + '.bin', 'wb') as f:
            f.write(data)

        with subprocess.Popen([
                'fake_yaz0.exe',
                _common.TEMP_FILE_NAME + '.bin',
                _common.TEMP_FILE_NAME + '.szs',
                ]) as proc:
            proc.communicate()

        os.remove(_common.TEMP_FILE_NAME + '.bin')

        with open(_common.TEMP_FILE_NAME + '.szs', 'rb') as f:
            packed = f.read()

        os.remove(_common.TEMP_FILE_NAME + '.szs')

    return packed


def _compressYAZ0COMP(data):
    """
    Run this data through YAZ0COMP
    """

    if not data:
        # This is a zero-length file, which YAZ0COMP would choke on.
        # Just return a stock empty Yaz0 file manually.
        return b'Yaz0\0\0\0\0\0\0\0\0\0\0\0\0'

    # YAZ0COMP usage instructions:
    # 1) Put the uncompressed data into a file called "unp"
    # 2) Call YAZ0COMP.EXE (no arguments)
    # 3) The compressed data is put into a file called "!out".

    with _common.cwdAsPathTo(__file__):

        with open('unp', 'wb') as f:
            f.write(data)

        with _common.getDevNull() as devnull:
            with subprocess.Popen('YAZ0COMP.EXE', stdout=devnull) as proc:
                proc.communicate()

        os.remove('unp')

        with open('!out', 'rb') as f:
            packed = f.read()

        os.remove('!out')

    return packed
