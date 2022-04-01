#!/usr/bin/env python3
# vim: set expandtab tabstop=4 shiftwidth=4:

# Copyright 2022 Christopher J. Kucera
# <cj@apocalyptech.com>
# <http://apocalyptech.com/contact.php>
#
# PyOakTMS is free software: you can redistribute it
# and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of
# the License, or (at your option) any later version.
#
# PyOakTMS is distributed in the hope that it will
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
import datetime

def tms_sort(s):
    """
    This util strives to write out OakTMS files as close to GBX's as possible.
    The locres dirs we see in the `Content/Localization` dir seem to be
    alphabetized how we'd hope, but at `OakGame`, we seem to always see `TMS`
    before `Content`.  So this function basically just looks for `OakGame/TMS/`
    in the string and substitutes `OakGame/\tTMS` (tabs are about the lowest-
    sorted character, I think).
    """
    return s.replace(f'OakGame{os.path.sep}TMS{os.path.sep}',
            f"OakGame{os.path.sep}\tTMS{os.path.sep}", 1)

class DataFile:
    """
    Class to wrap some of our data-writing functions into.
    """

    def __init__(self, filename=None, df=None):
        """
        If we're passed a filename, open the file for writing in binary.  If
        we're passed a filehandle instead, just use that.  (For our purposes,
        it'll probably be an io.BytesIO object.)
        """
        self.filename = filename
        if self.filename:
            self.df = open(self.filename, 'wb')
        else:
            self.df = df

    def close(self):
        self.df.close()

    def tell(self):
        return self.df.tell()

    def seek(self, offset, whence=io.SEEK_SET):
        self.df.seek(offset, whence)

    def read(self, size=-1):
        return self.df.read(size)

    def write(self, d):
        self.df.write(d)

    def uint32(self, value):
        """
        Writes a uint32 (four-byte) to the file
        """
        self.df.write(struct.pack('<I', value))

    def ulong64(self, value):
        """
        Writes a ulong64 (eight-byte) to the file
        """
        self.df.write(struct.pack('<Q', value))

    def str(self, value):
        """
        Writes a string (zero-terminated *and* with a uint32 length
        parameter in front, which includes the null byte) to the
        specified file, utf-8-encoded.  Note that the stored length
        is byte length, not necessarily string length.

        (TODO: I'm not *actually* sure about that, at time of
        writing, but that's how the string-reading function in my
        main `oaktms.py` handles lengths)
        """
        bytes_val = value.encode('utf-8') + b"\00"
        self.uint32(len(bytes_val))
        self.df.write(bytes_val)

    def write_file(self, filename, data):
        """
        Writes a file to the file, using the specifified
        name and data.  A string filename will be written first,
        followed by a uint32 size of the file, followed by the
        contents.
        """
        self.str(filename)
        self.uint32(len(data))
        self.df.write(data)

def main():

    # Arguments!
    parser = argparse.ArgumentParser(
            description='Pack OakTMS Files',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            )

    parser.add_argument('-m', '--magic',
            type=int,
            default=0x9E2A83C1,
            help='Magic number (identical for Oak and Daffodil)',
            )

    parser.add_argument('-c', '--chunksize',
            type=int,
            default=131072,
            help='Chunk size to use in the TMS file',
            )

    parser.add_argument('-p', '--prefix',
            type=str,
            default='../../..',
            help='Common prefix to prepend to raw OakTMS paths',
            )

    parser.add_argument('-d', '--date',
            type=str,
            help='Datetime (MM/DD/YY HH:MM:SS) to report in the footer (defaults to current time)',
            )

    parser.add_argument('--footer1',
            type=str,
            default='cbauer',
            help='First "footer" line to add (purpose unknown)',
            )

    parser.add_argument('--footer2',
            type=str,
            default='CBAUER-Q42',
            help='Second "footer" line to add (purpose unknown)',
            )

    parser.add_argument('--footer-num1',
            type=int,
            default=0,
            help='First "footer" number to add (purpose unknown)',
            )

    parser.add_argument('--footer-num2',
            type=int,
            default=0,
            help='Second "footer" number to add (purpose unknown)',
            )

    parser.add_argument('-o', '--output',
            type=str,
            help='Output file (defaults to the name of the dir with `.cfg` appended)',
            )

    parser.add_argument('-f', '--force',
            action='store_true',
            help='Force overwrite of file (will prompt, otherwise)',
            )

    parser.add_argument('-v', '--verbose',
            action='store_true',
            help='Verbose output (just adds filename listing)',
            )

    parser.add_argument('dirname',
            nargs=1,
            help='Directory to pack into OakTMS file (the directory name itself will not be included)',
            )

    # Parse args
    args = parser.parse_args()
    if not args.date:
        now = datetime.datetime.now()
        args.date = now.strftime('%m/%d/%y %H:%M:%S')
    args.dirname = args.dirname[0]
    if not args.output:
        args.output = f'{args.dirname}.cfg'

    # Make sure the directory exists
    if not os.path.exists(args.dirname):
        print(f'ERROR: {args.dirname} does not exist')
        sys.exit(1)

    # Get a list of files to process
    filelist = []
    for dirpath, _, filenames in os.walk(args.dirname):
        for filename in filenames:
            filelist.append(os.path.join(dirpath, filename))
    if not filelist:
        print(f'ERROR: No files found in {args.dirname}')
        sys.exit(1)
    filelist.sort(key=tms_sort)
    if len(filelist) == 1:
        plural = ''
    else:
        plural = 's'
    print(f'Compressing {len(filelist)} file{plural} to {args.output}')

    # Check to see if the output file exists.  If so, delete it
    # so long as the user has said to do so.
    if os.path.exists(args.output):
        if not args.force:
            while True:
                print(f'{args.output} already exists - overwrite?')
                resp = input('[y]es/[N]o> ').strip().lower()
                if resp == '' or resp == 'n':
                    print('Exiting!')
                    sys.exit(2)
                elif resp == 'y':
                    break
        os.unlink(args.output)

    # Get our file data concatenated properly
    file_data = DataFile(df=io.BytesIO())
    strip_len = len(args.dirname)
    for filename_local in filelist:
        filename_label = args.prefix + filename_local[strip_len:]
        if os.path.sep == '\\':
            filename_label = filename_label.replace('\\', '/')
        if args.verbose:
            print(f'   {filename_label}')
        with open(filename_local, 'rb') as df:
            file_data.write_file(filename_label, df.read())
    total_uncomp_size = file_data.tell()
    file_data.seek(0)

    # Split the file data into chunks and compress.  `chunks` contains tuples:
    #   idx 0: uncompressed size
    #   idx 1: compressed size
    #   idx 2: compressed data
    chunks = []
    total_comp_size = 0
    while file_data.tell() < total_uncomp_size:
        to_read = min(args.chunksize, total_uncomp_size - file_data.tell())
        chunk_data_comp = zlib.compress(file_data.read(to_read))
        chunks.append((to_read, len(chunk_data_comp), chunk_data_comp))
        total_comp_size += chunks[-1][1]

    # Now start writing out the actual file
    tms = DataFile(filename=args.output)

    # Initial data
    tms.uint32(total_uncomp_size)
    tms.uint32(len(filelist))
    tms.ulong64(args.magic)
    tms.ulong64(args.chunksize)
    tms.ulong64(total_comp_size)
    tms.ulong64(total_uncomp_size)

    # Chunk info, then chunks
    for uncomp_size, comp_size, _ in chunks:
        tms.ulong64(comp_size)
        tms.ulong64(uncomp_size)
    for _, _, chunk_data in chunks:
        tms.write(chunk_data)
    
    # Footer
    tms.uint32(3)
    tms.str(args.date)
    tms.str(args.footer1)
    tms.str(args.footer2)
    tms.uint32(args.footer_num1)
    tms.uint32(args.footer_num2)

    # ... and close!
    tms.close()
    file_data.close()
    print('Done!')

if __name__ == '__main__':
    main()

