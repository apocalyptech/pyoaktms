Borderlands 3 Python OakTMS/DaffodilTMS Extractor
=================================================

This is a little commandline Python script to extract Borderlands 3 OakTMS
and Tiny Tina's Wonderlands DaffodilTMS files.  (The format is identical
for both games.)  The OakTMS/DaffodilTMS file is the first bit of
network configuration that happens when BL3 launches, and serves as the
springboard for connecting to all of GBX's online services, including hotfixes and the like.

Borderlands 2 + TPS have a similar SparkTMS configuration starting point,
which can be extracted with [gibbed's SparkTmsUnpack](https://github.com/gibbed/Gibbed.Borderlands2/blob/master/projects/Gibbed.Borderlands2.SparkTmsUnpack/Program.cs)
application (available in his `all_tools` zipfiles on his
[releases page](https://github.com/gibbed/Gibbed.Borderlands2/releases)).
There's a few differences between the BL2/TPS and BL3 versions, though.

Known URLs for OakTMS files are:

**BL3**
- http://cdn.services.gearboxsoftware.com/sparktms/oak/pc/steam/OakTMS-prod.cfg
- http://cdn.services.gearboxsoftware.com/sparktms/oak/pc/steam/OakTMS-qa.cfg
- http://cdn.services.gearboxsoftware.com/sparktms/oak/pc/epic/OakTMS-prod.cfg
- http://cdn.services.gearboxsoftware.com/sparktms/oak/pc/epic/OakTMS-qa.cfg

**Tiny Tina's Wonderlands**
- http://cdn.services.gearboxsoftware.com/sparktms/daffodil/pc/epic/DaffodilTMS-prod.cfg
- http://cdn.services.gearboxsoftware.com/sparktms/daffodil/pc/epic/DaffodilTMS-qa.cfg

It'd be nice to figure out the URLs for console versions, so we can find
out if there's any differences between the two.  I assume endianness would
likely be different.

Usage
-----

Install Python 3.x (tested on 3.9+), download the script, and run it from a
commandline (terminal, `cmd.exe`, Powershell, what have you).  Using the `--help`
option will give you this output:

    usage: oaktms.py [-h] [-v] [-l] [-f] [-d DIRECTORY] filename

    Extract OakTMS Files

    positional arguments:
      filename              OakTMS file to parse

    optional arguments:
      -h, --help            show this help message and exit
      -v, --verbose         Verbose output (specify twice, for extra debug output)
      -l, --list            Only list file contents
      -f, --force           Force overwrite of file contents (will prompt,
                            otherwise)
      -d DIRECTORY, --directory DIRECTORY
                            Directory to extract to (will default to the base
                            filename of the OakTMS file)

.locres Parsing
---------------

This repo also contains `locres.py`, which can be used to view the contents of
the `*.locres` files which make up the bulk of BL3's OakTMS contents.  This
implementation is based on [klimaleksus's UE4-locres-Online-Editor](https://github.com/klimaleksus/UE4-locres-Online-Editor),
and you should check that project out if you want a better implementation.
The one here is pretty rough-n-ready, and happens to work fine on the BL3
`.locres` files I've tried so far, but almost certainly has some edge cases
which would cause failures.

Repacking
---------

As of April 2022, this repo also includes a utility to re-pack a directory
into a new OakTMS/DaffodilTMS file.  Its `--help` output looks like this:

    usage: pack-oaktms.py [-h] [-m MAGIC] [-c CHUNKSIZE] [-p PREFIX] [-d DATE]
                          [--footer1 FOOTER1] [--footer2 FOOTER2]
                          [--footer-num1 FOOTER_NUM1] [--footer-num2 FOOTER_NUM2]
                          [-o OUTPUT] [-f] [-v]
                          dirname

    Pack OakTMS Files

    positional arguments:
      dirname               Directory to pack into OakTMS file (the directory name
                            itself will not be included)

    options:
      -h, --help            show this help message and exit
      -m MAGIC, --magic MAGIC
                            Magic number (identical for Oak and Daffodil)
                            (default: 2653586369)
      -c CHUNKSIZE, --chunksize CHUNKSIZE
                            Chunk size to use in the TMS file (default: 131072)
      -p PREFIX, --prefix PREFIX
                            Common prefix to prepend to raw OakTMS paths (default:
                            ../../..)
      -d DATE, --date DATE  Datetime (MM/DD/YY HH:MM:SS) to report in the footer
                            (defaults to current time) (default: None)
      --footer1 FOOTER1     First "footer" line to add (purpose unknown) (default:
                            cbauer)
      --footer2 FOOTER2     Second "footer" line to add (purpose unknown)
                            (default: CBAUER-Q42)
      --footer-num1 FOOTER_NUM1
                            First "footer" number to add (purpose unknown)
                            (default: 0)
      --footer-num2 FOOTER_NUM2
                            Second "footer" number to add (purpose unknown)
                            (default: 0)
      -o OUTPUT, --output OUTPUT
                            Output file (defaults to the name of the dir with
                            `.cfg` appended) (default: None)
      -f, --force           Force overwrite of file (will prompt, otherwise)
                            (default: False)
      -v, --verbose         Verbose output (just adds filename listing) (default:
                            False)

The vast majority of those options should be safe to leave at the defaults,
but you can tweak every aspect of the resulting TMS file if you like.  Repacking
a freshly-extracted TMS file should result in a binary-identical new file.  The
various "footer" information (including the `date`) is pretty likely to be
there just for informational purposes for any human looking at the file.
The TMS compilation/build date, host, and build number, perhaps?  I
picked an effectively random value for what looks like a build number, as the
default. 

The file ends with eight bytes which, so far, have always been zeroes.  I've
chosen to interpret those as two uint32s, and you can set their values with
`--footer-num1` and `--footer-num2`, but you're probably best off leaving them
at their default `0` values.

The "magic" number is found in the header of both OakTMS and DaffodilTMS files,
and is the same for both.  No idea how the game would respond if this was
changed.  The `chunksize` parameter is the chunks of uncompressed data which
will be individually compressed using zlib.

TODO
----

- I'm not sure if this works properly on Windows.  I may have to do some
  fiddling with the path separators.  Let me know!
- As mentioned above, it'd be nice to get some console OakTMS files to verify
  how those look.
- I should really adapt this to use [Kaitai Struct](https://kaitai.io/).

Changelog
---------

- **April 1, 2022**
  - Added util to repack TMS files, and made a note of the DaffodilTMS files
    that Wonderlands uses (turns out to be identical to OakTMS)

- **Feb 13, 2021**
  - Tightened up input processing when overwrite confirmation is triggered
  - Provide notification when the extraction dir is set to the current dir
    (which happens when the util is passed a TMS file with no file extension)

- **Feb 12, 2021**
  - Initial release

License
-------

PyOakTMS is licensed under the [GPLv3 or later](https://www.gnu.org/licenses/quick-guide-gplv3.html).
See [COPYING.txt](COPYING.txt) for the full text of the license.

