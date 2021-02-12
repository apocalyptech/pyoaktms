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

import io
import os
import sys
import zlib
import struct
import argparse

class TMSArchive:
    """
    Silly little class to hold the files that we've extracted from
    an OakTMS file.

    Known OakTMS URLs (would be interested to figure out what the console versions
    are, assuming they do the same thing):

    http://cdn.services.gearboxsoftware.com/sparktms/oak/pc/steam/OakTMS-prod.cfg
    http://cdn.services.gearboxsoftware.com/sparktms/oak/pc/steam/OakTMS-qa.cfg
    http://cdn.services.gearboxsoftware.com/sparktms/oak/pc/epic/OakTMS-prod.cfg
    http://cdn.services.gearboxsoftware.com/sparktms/oak/pc/epic/OakTMS-qa.cfg

    As of writing, Steam+EGS versions are identical, as you'd hope.
    """

    def __init__(self, filename, verbose=False):

        self.filename = filename
        self.files = {}
        self.verbose = verbose
        self.common_prefix = ''
        self._process()

    def _process(self):
        """
        Process the file (read in all the info)
        """

        file_stat = os.stat(self.filename)
        total_size = file_stat.st_size
        if self.verbose:
            print('File size: {}'.format(total_size))

        with open(self.filename, 'rb') as df:

            total_uncomp_size = self._uint32(df)
            if self.verbose:
                print('Total uncompressed size: {}'.format(total_uncomp_size))
            filecount = self._uint32(df)
            if self.verbose:
                print('File count: {}'.format(filecount))

            sig = self._ulong64(df)
            assert(sig == 0x9E2A83C1)

            chunk_size = self._ulong64(df)
            if self.verbose:
                print('Chunk size: {}'.format(chunk_size))

            total_comp_size = self._ulong64(df)
            new_uncomp_size = self._ulong64(df)
            assert(new_uncomp_size == total_uncomp_size)

            chunk_sizes = []
            cur_comp_size = 0
            cur_uncomp_size = 0
            while True:

                chunk_comp_size = self._ulong64(df)
                chunk_uncomp_size = self._ulong64(df)
                cur_comp_size += chunk_comp_size
                cur_uncomp_size += chunk_uncomp_size

                if self.verbose:
                    print('Got chunk, compressed: {}, uncompressed: {}'.format(chunk_comp_size, chunk_uncomp_size))
                chunk_sizes.append((chunk_comp_size, chunk_uncomp_size))
                if cur_comp_size == total_comp_size:
                    assert(cur_uncomp_size == total_uncomp_size)
                    break
                assert(cur_comp_size < total_comp_size)
                assert(cur_uncomp_size < total_uncomp_size)

            if self.verbose:
                print('Got {} zlib chunks'.format(len(chunk_sizes)))

            # Read in the chunks
            data_list = []
            for chunk_comp_size, chunk_uncomp_size in chunk_sizes:
                data_list.append(zlib.decompress(df.read(chunk_comp_size)))
            data = b''.join(data_list)
            assert(len(data) == total_uncomp_size)

            # Read in the footer info
            num_strs = self._uint32(df)
            for idx in range(num_strs):
                footer_str = self._str(df)
                if self.verbose:
                    print('Footer string {}: {}'.format(idx+1, footer_str))
            footer_num_1 = self._uint32(df)
            footer_num_2 = self._uint32(df)
            if self.verbose:
                print('Footer num 1: {}'.format(footer_num_1))
                print('Footer num 2: {}'.format(footer_num_2))
            assert(df.tell() == total_size)

            # Now process the decompressed data
            idf = io.BytesIO(data)

            idf.seek(0, io.SEEK_END)
            if self.verbose:
                print('Total bytes in zlib-decompressed area: {}'.format(idf.tell()))
            idf.seek(0)

            for _ in range(filecount):
                filename, contents = self._read_file(idf)
                self.files[filename] = contents
                if self.verbose:
                    print('Raw TMS filename found: {}'.format(filename))
            self._finish()

            assert(idf.tell() == total_uncomp_size)

    def _uint32(self, df):
        """
        Reads a uint32 (four-byte) from the specified file
        """
        return struct.unpack('<I', df.read(4))[0]

    def _ulong64(self, df):
        """
        Reads a ulong64 (eight-byte) from the specified file
        """
        return struct.unpack('<Q', df.read(8))[0]

    def _str(self, df):
        """
        Reads a string (zero-terminated *and* with a uint32 length
        parameter in front) from the specified file
        """
        strlen = self._uint32(df)
        return df.read(strlen)[:-1].decode('utf-8')

    def _read_file(self, df):
        """
        Read a file entry from the specified file.  A string filename
        should be first, followed by a uint32 size of the file, followed
        by the file contents.  Will return a tuple of the filename and
        contents.
        """
        filename = self._str(df)
        contents_len = self._uint32(df)
        contents = df.read(contents_len)
        return (filename, contents)

    def _finish(self):
        """
        "Finishes" the archive once we've read in all the files, which
        is basically just finding a common path prefix which we can strip
        out while extracting the files.  Will only strip out common `..`
        entries.
        """

        # Find the common prefix (though we're only stripping out `..`s)
        prefixes = []
        for prefix in os.path.commonpath(self.files.keys()).split('/'):
            if prefix == '..':
                prefixes.append('..')
            else:
                break
        if len(prefixes) > 0:
            prefixes.append('')
        self.common_prefix = '/'.join(prefixes)
        if self.verbose:
            print('Found common filename prefix: {}'.format(self.common_prefix))

        # If there are any files with `..` left in them, after stripping
        # off the common prefixes, abort.  Don't want to have to cope
        # with dealing with extractions which have relative paths.
        new_files = {}
        for filename, contents in self.files.items():
            new_filename = filename[len(self.common_prefix):]
            if '../' in new_filename:
                raise RuntimeError('Relative path not allowed in stripped filename: {}'.format(new_filename))
            new_files[new_filename] = contents
        self.files = new_files

    def __len__(self):
        return len(self.files)

    def __iter__(self):
        for i in self.files.items():
            yield i

if __name__ == '__main__':

    # Arguments!
    parser = argparse.ArgumentParser(
            description='Extract OakTMS Files',
            )

    parser.add_argument('-v', '--verbose',
            action='count',
            default=0,
            help='Verbose output (specify twice, for extra debug output)',
            )

    parser.add_argument('-l', '--list',
            action='store_true',
            help='Only list file contents',
            )

    parser.add_argument('-f', '--force',
            action='store_true',
            help='Force overwrite of file contents (will prompt, otherwise)',
            )

    parser.add_argument('-d', '--directory',
            type=str,
            help='Directory to extract to (will default to the base filename of the OakTMS file)',
            )

    parser.add_argument('filename',
            nargs=1,
            help='OakTMS file to parse',
            )

    # Parse args
    args = parser.parse_args()
    filename = args.filename[0]
    verbose = args.verbose >= 1
    debug = args.verbose >= 2
    force = args.force
    extract_dir = args.directory

    # Process the archive
    tms = TMSArchive(filename, verbose=debug)

    # List or Extract
    if args.list:
        if verbose:
            print('{} contents:'.format(filename))
            print('')
            for filename, _ in tms:
                print(filename)
            print('')
        else:
            for filename, _ in tms:
                print(filename)
    else:
        # Figure out our extraction dir, if needed
        if not extract_dir:
            extract_dir, ext = os.path.splitext(filename)
            if extract_dir == filename:
                extract_dir = '.'

        # Loop through and extract
        for int_filename, contents in tms:
            base_dirname, base_filename = os.path.split(int_filename)
            dirname = '/'.join([extract_dir, base_dirname])
            full_filename = '/'.join([dirname, base_filename])
            os.makedirs(dirname, exist_ok=True)
            if not force and os.path.exists(full_filename):
                print('{} already exists - overwrite?'.format(full_filename))
                resp = input('[y]es/[N]o/[a]lways/[q]uit> '.format(full_filename)).strip().lower()
                if resp == '':
                    resp = 'n'

                if resp== 'n':
                    print('Skipping!')
                    continue
                elif resp == 'q':
                    print('Exiting!')
                    sys.exit(1)
                elif resp == 'a':
                    force = True

            # Do the actual writing
            if verbose:
                print('Writing to {}...'.format(full_filename))
            with open(full_filename, 'wb') as odf:
                odf.write(contents)

        # Report
        print('Extracted {} to {}'.format(filename, extract_dir))

