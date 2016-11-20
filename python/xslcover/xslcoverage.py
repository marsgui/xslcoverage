#
# XSL Coverage - See COPYRIGHT
#
import os
import sys
import glob
import traceback
import runner
import runcover
import xmlcover
from xmlcover import CoverAnalyzer, TraceLog
from runcover import CoverageRunner

class ErrorHandler:
    def __init__(self):
        self._dump_stack = False
        self.rc = 0

    def dump_stack(self, dump=True):
        self._dump_stack = dump

    def failure_track(self, msg, rc=1):
        self.rc = rc
        print >>sys.stderr, (msg)
        if self._dump_stack:
            traceback.print_exc()

    def failed_exit(self, rc=1):
        self.failure_track(msg, rc)
        sys.exit(self.rc)


class BasicCmd:
    def __init__(self):
        pass
    def setup_parser(self, parser):
        return True
    def help(self, cmd):
        if self.__doc__:
            return self.__doc__
        else:
            return None
    def run(self, parser, args):
        pass


class RunCoverageCmd(BasicCmd):
    """
    Call the runner that will create some coverage traces
    """
    def __init__(self, coverage):
        self.coverage = coverage
        self.runners = runner.get_plugins()

    def _inherit_options(self, args):
        args.trace_dir = self.coverage.trace_dir
        args.report = False

    def setup_parser(self, parser):
        parser.add_argument("runner",
            help="Trace generator. Known runners: %s" % ", ".join(self.runners))
        parser.add_argument("--no-snapshot", action="store_false",
            dest="snapshot", default=True,
            help="Do not create a dated subdirectory containing the traces")
        # parser.add_argument("--report", action="store_true",
        #    help="Build the HTML coverage report from the run")

    def run(self, parser, args):
        self._inherit_options(args)
        try:
            command = runner.load_runner(args.runner)
        except Exception, e:
            print e
            return

        rc, cover_runner = runcover.cmdline_runargs(command, args,
                                                    args.remain_args)
        self.coverage.cover_runner = cover_runner

        if rc != 0:
            print >> sys.stderr, "Command failed (rc=%d)" % rc
            self.coverage.allow_report = False


class ReportCoverageCmd(BasicCmd):
    """
    Make a coverage report from a tracelog or traces files
    """
    def __init__(self, coverage):
        self.coverage = coverage

    def _inherit_options(self, args):
        args.trace_dir = self.coverage.trace_dir

    def setup_parser(self, parser):
        parser.add_argument("-f", "--from-log",
                            help="Trace report of the traces")
        parser.add_argument("--show-stats", action="store_true",
                            help="Show coverage statistics on console")
        parser.add_argument("-O", "--html-dir",
                            help="Directory containing the HTML output")

    def run(self, parser, args):
        self._inherit_options(args)
        if not(self.coverage.allow_report):
            return

        if self.coverage.cover_runner:
            r = self.coverage.cover_runner
            r.build_coverage_report(html_dir=args.html_dir,
                                    print_stats=args.show_stats)
        else:
            xmlcover.cmdline_runargs(args, args.remain_args)


class XslCoverageCommand:
    def __init__(self):
        self._commands = [
            ("run", RunCoverageCmd),
            ("report", ReportCoverageCmd)
        ]
        self.commands_to_run = []
        self.trace_dir = ""
        self.cover_runner = None
        self.allow_report = True
        self.options = None

    def commands(self):
        return [c[0] for c in self._commands]

    def setup_options(self, parser):
        parser.add_argument("--trace-dir", default="",
              help="Base directory where the traces are stored")
        parser.add_argument("--dump-stack", action="store_true",
              help="Dump error stack (debug purpose)")

    def setup_parser(self, parser):
        self.setup_options(parser)

        if not(self._commands):
            return
        partial = True
        subparsers = parser.add_subparsers() #title=title)
        clsused = []
        cmdobjs = []
        for cmd, cls in self._commands:
            # Don't duplicate objects used for several commands
            if cls in clsused:
                cmdobj = cmdobjs[clsused.index(cls)]
            else:
                cmdobj = cls(self)
                cmdobjs.append(cmdobj)
                clsused.append(cls)
            kwargs = {}
            if cmdobj.help(cmd):
                kwargs["help"] = cmdobj.help(cmd)
            p = subparsers.add_parser(cmd, **kwargs)
            partial = cmdobj.setup_parser(p) or partial
            p.set_defaults(run=cmdobj.run, name=cmd)
        return partial

    def prepare(self, parser, argslist):
        self.options = argslist[0]
        self.trace_dir = self.options.trace_dir

        # Sort the commands in the right order
        cmds = [ args.name for args in argslist ]
        self.commands_to_run = []
        for cmd in self.commands():
            if cmd in cmds:
                i = cmds.index(cmd)
                self.commands_to_run.append(argslist[i])
        
    def cleanup(self):
        pass

    def _commands_in_args(self, commands, args):
        for c in commands:
            if c in args:
                return True
        return False

    def run(self, parser):
        args, remain_args =  parser.parse_known_args()
        args.remain_args = remain_args
     
        argslist = [args]
        commands = self.commands()
        while remain_args and self._commands_in_args(commands, remain_args):
            args, remain_args =  parser.parse_known_args(remain_args)
            args.remain_args = remain_args
            argslist.append(args)

        self.prepare(parser, argslist)
        for args in self.commands_to_run:
            args.run(parser, args)


def main():
    from argparse import ArgumentParser
    parser = ArgumentParser(description='This script computes XSL Coverage')

    coverage = XslCoverageCommand()
    coverage.setup_parser(parser)

    error = ErrorHandler()

    try:
        coverage.run(parser)
    except Exception, e:
        if coverage.options and coverage.options.dump_stack:
            error.dump_stack()
        error.failure_track("Error: '%s'" % (e))

    coverage.cleanup()
    sys.exit(error.rc)


if __name__ == "__main__":
    main()
