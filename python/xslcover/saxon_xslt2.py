#
# XSL Coverage - See COPYRIGHT
#
import os
import sys
from runners.saxon import SaxonRunner
from runners.saxon9he import Saxon9heRunner

def main(saxon_version="6"):
    from argparse import ArgumentParser
    parser = ArgumentParser(description='XSLT engine with traces')
    parser.add_argument("-D", "--trace-dir", default="",
          help="Directory containing the traces")
    parser.add_argument("-V", "--saxon-version", default=saxon_version,
          choices=["6", "6.5.5", "9", "9he"],
          help="Version of Saxon to use")

    options, remain_args =  parser.parse_known_args()

    if not(options.trace_dir):
        options.trace_dir = os.environ.get("TRACE_DIRECTORY", "")

    if options.saxon_version.startswith("6"):
        s = SaxonRunner()
    elif options.saxon_version.startswith("9"):
        s = Saxon9heRunner()

    rc = s.run(remain_args, trace_dir=options.trace_dir)
    sys.exit(rc)
 

if __name__ == "__main__":
    main()
