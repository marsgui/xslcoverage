#
# XSL Coverage - See COPYRIGHT
#
import os
import sys
from runners.saxon import TraceSaxon

def main():
    from argparse import ArgumentParser
    parser = ArgumentParser(description='XSLT engine with traces')
    parser.add_argument("-D", "--trace-dir", default="",
          help="Directory containing the traces")

    options, remain_args =  parser.parse_known_args()

    if not(options.trace_dir):
        options.trace_dir = os.environ.get("TRACE_DIRECTORY", "")

    s = TraceSaxon()
    rc = s.run(remain_args, trace_dir=options.trace_dir)
    sys.exit(rc)
 

if __name__ == "__main__":
    main()
