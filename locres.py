#!/usr/bin/env python3
# vim: set expandtab tabstop=4 shiftwidth=4:

# Copyright 2021 Christopher J. Kucera
# <cj@apocalyptech.com>
# <http://apocalyptech.com/contact.php>
#
# PyOakTMS is free software: you can redistribute it
# and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of
# the License, or (at your option) any later version.
#
# Borderlands 3 Hotfix Modding Library is distributed in the hope that it will
# be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PyOakTMS.  If not, see <https://www.gnu.org/licenses/>.

import sys
import struct
import argparse

# Credits to https://github.com/klimaleksus/UE4-locres-Online-Editor for
# having already figured this out!

# This app isn't especially nicely put together, sorry for the excess
# of mess and scoping violations!  Also doesn't really fully parse the
# header; this implementation might fail in some circumstances (it
# works for the BL3 .locres files that I've tried, though, so that's
# good enough for me).

def _uint32(df):
    return struct.unpack('<I', df.read(4))[0]

def _uint64(df):
    return struct.unpack('<Q', df.read(8))[0]

def _int32(df):
    return struct.unpack('<i', df.read(4))[0]

def _str(df):
    strlen = _int32(df)
    if strlen == 0:
        return ''
    elif strlen > 0:
        return df.read(strlen)[:-1].decode('utf-8')
    else:
        return df.read(abs(strlen)*2)[:-2].decode('utf-16le')

class Key:

    def __init__(self, namespace, df):
        self.namespace = namespace
        self.key = _str(df)
        self.idnum = _uint32(df)
        self.number = _int32(df)
        self.line = None
        if self.number < 0:
            self.line = _str(df)
            self.number = -1

class Namespace:

    def __init__(self, df):
        self.name = _str(df)
        self.keys = []
        num_keys = _uint32(df)
        for _ in range(num_keys):
            self.keys.append(Key(self, df))

if __name__ == '__main__':

    parser = argparse.ArgumentParser(
            description='Display .locres contents',
            )
    parser.add_argument('filename',
            nargs=1,
            help='Filename to parse',
            )
    args = parser.parse_args()
    filename = args.filename[0]

    namespaces = []
    strings = []
    with open(filename, 'rb') as df:
        # Fudging a bit here.
        df.seek(0x19)
        namespace_count = _uint32(df)
        for _ in range(namespace_count):
            namespaces.append(Namespace(df))

        string_count = _uint32(df)
        for _ in range(string_count):
            strings.append(_str(df))

    for ns in namespaces:
        label = 'Namespace "{}"'.format(ns.name)
        print(label)
        print('='*len(label))
        print('')
        for key in ns.keys:
            print(key.key)
            print(strings[key.number])
            print('')

