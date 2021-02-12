Borderlands 3 Python OakTMS Extractor
=====================================

This is a little commandline Python script to extract Borderlands 3
OakTMS files.  The OakTMS file is the first bit of network configuration that
happens when BL3 launches, and serves as the springboard for connecting to all
of GBX's online services, including hotfixes and the like.

Borderlands 2 + TPS have a similar SparkTMS configuration starting point,
which can be extracted with [gibbed's SparkTmsUnpack](https://github.com/gibbed/Gibbed.Borderlands2/blob/master/projects/Gibbed.Borderlands2.SparkTmsUnpack/Program.cs)
application (available in his `all_tools` zipfiles on his
[releases page](https://github.com/gibbed/Gibbed.Borderlands2/releases)).
There's a few differences between the BL2/TPS and BL3 versions, though.

Known URLs for OakTMS files are:

- http://cdn.services.gearboxsoftware.com/sparktms/oak/pc/steam/OakTMS-prod.cfg
- http://cdn.services.gearboxsoftware.com/sparktms/oak/pc/steam/OakTMS-qa.cfg
- http://cdn.services.gearboxsoftware.com/sparktms/oak/pc/epic/OakTMS-prod.cfg
- http://cdn.services.gearboxsoftware.com/sparktms/oak/pc/epic/OakTMS-qa.cfg

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

TODO
----

- I'm not sure if this works properly on Windows.  I may have to do some
  fiddling with the path separators.  Let me know!
- As mentioned above, it'd be nice to get some console OakTMS files to verify
  how those look.
- I should really adapt this to use [Kaitai Struct](https://kaitai.io/).

Changelog
---------

- **Feb 12, 2021**
  - Initial release

License
-------

PyOakTMS is licensed under the [GPLv3 or later](https://www.gnu.org/licenses/quick-guide-gplv3.html).
See [COPYING.txt](COPYING.txt) for the full text of the license.

