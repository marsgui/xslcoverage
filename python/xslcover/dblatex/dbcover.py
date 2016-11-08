#
# XSL Coverage - See COPYRIGHT
#
import os
import sys
from subprocess import Popen
from xslcover.runcover import cmdline_parser, cmdline_runargs

class TraceDblatex:
    def __init__(self, dblatex="dblatex"):
        self.dblatex = dblatex
        self.cmd = []

    def run(self, args, trace_dir=""):
        cmd = [self.dblatex, "-T", "xsltcover"]
        cmd += args
        self.cmd = cmd

        # Extend the dblatex config dir, to find the xsltcover.conf file
        config_dir = os.environ.get("DBLATEX_CONFIG_FILES", "")
        if config_dir:
            pathsep = os.pathsep
        else:
            pathsep = ""
        config_dir += pathsep + os.path.abspath(os.path.dirname(__file__))
        env = {}
        env.update(os.environ)
        env.update({"DBLATEX_CONFIG_FILES": config_dir})

        # Specify the trace directory used by saxon_xslt2
        if trace_dir:
            env.update({ "TRACE_DIRECTORY": trace_dir })

        try:
            p = Popen(cmd, env=env)
            rc = p.wait()
        except OSError, e:
            print >> sys.stderr, "dblatex seems to be missing: %s" % (e)
            rc = -1
        return rc

def main():
    from argparse import ArgumentParser

    parser = ArgumentParser(description='Run dblatex with traces')
    parser = cmdline_parser(parser=parser)
    parser.add_argument("--dblatex", help="Script to call", default="dblatex")
    options, remain_args = parser.parse_known_args()

    command = TraceDblatex(options.dblatex)

    cmdline_runargs(command, options, remain_args)


if __name__ == "__main__":
    main()
