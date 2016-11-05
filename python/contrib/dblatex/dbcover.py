import os
from subprocess import Popen
from runcover import cmdline_parser, cmdline_runargs

class TraceDblatex:
    def __init__(self, dblatex="dblatex"):
        self.dblatex = dblatex
        self.cmd = []

    def run(self, args, trace_dir=""):
        cmd = [self.dblatex, "-T", "xsltcover"]
        cmd += args
        self.cmd = cmd
        if trace_dir:
            env = {}
            env.update(os.environ)
            env.update({ "TRACE_DIRECTORY": trace_dir })
        else:
            env = None

        p = Popen(cmd, env=env)
        rc = p.wait()
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
