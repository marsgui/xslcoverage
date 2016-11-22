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


class TraceRunner(TraceDblatex):
    "Plugin Class to load"


