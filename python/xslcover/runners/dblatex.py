#
# XSL Coverage - See COPYRIGHT
#
import os
import sys
from subprocess import Popen
from argparse import ArgumentParser
from xslcover.coverapi import TraceRunnerBase


class TraceDblatex(TraceRunnerBase):
    def __init__(self):
        self.dblatex = "dblatex"
        self.config_dir = os.path.abspath(os.path.dirname(__file__))
        self.cmd = []

    def _parse_args(self, args):
        parser = ArgumentParser(description='Run dblatex with traces')
        parser.add_argument("--script", help="Script to call",
                            default="dblatex")
        options, remain_args = parser.parse_known_args(args)
        self.dblatex = options.script
        return remain_args

    def trace_generator(self):
        # FIXME
        return "saxon"

    def run(self, args, trace_dir=""):
        args = self._parse_args(args)

        # Prepend the arguments to use xsltcover.conf (need dblatex >= 0.3.10)
        cmd = [self.dblatex, "-c",
               os.path.join(self.config_dir, "xsltcover.conf")]
        cmd += args
        self.cmd = cmd

        env = {}
        env.update(os.environ)

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


class TraceRunner(TraceDblatex):
    "Plugin Class to load"


