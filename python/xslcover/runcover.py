#
# XSL Coverage - See COPYRIGHT
#
import os
import glob
import xml.etree.ElementTree as ET
import hashlib
from datetime import datetime
from subprocess import Popen
from argparse import ArgumentParser
from xmlcover import CoverAnalyzer, TraceLog

class CoverageRunner:
    def __init__(self, snapshot=True, trace_dir="", command=None,
                       write_report=False):
        self.command = command
        self.trace_dir = os.path.abspath(trace_dir)
        self.snapshot = snapshot
        self.tracelog = None
        self.cover_report = None
        self.write_report = write_report

    def _prepare_tracedir(self):
        if (self.snapshot):
            now = datetime.now()
            snapdir = now.strftime("%y%j%H%M%S")
            self.trace_dir = os.path.join(self.trace_dir, snapdir)
            os.mkdir(self.trace_dir)
            self._old_files = []
        else:
            self._old_files = glob.glob(os.path.join(self.trace_dir, "*"))

    def _remove_tracedir(self):
        if not(self.snapshot):
            return
        _files = glob.glob(os.path.join(self.trace_dir, "*"))
        if not(_files):
            os.rmdir(self.trace_dir)
 
    def _write_tracelog(self):
        # Find out the files newly written
        trace_files = glob.glob(os.path.join(self.trace_dir, "*.xml"))
        for old_file in self._old_files:
            if old_file in trace_files:
                trace_files.remove(old_file)

        tracelog = TraceLog()
        tracelog.set_command(" ".join(self.command.cmd))
        tracelog.set_generator(self.command.trace_generator())
        for trace_file in trace_files:
            tracelog.add_trace(trace_file)

        stylesheets = []
        for trace_file in trace_files:
            tree = ET.parse(trace_file)
            root = tree.getroot()
            for item in root.iter("stylesheet"):
                stylesheet = item.get("file").replace("file:", "")
                if (stylesheet in stylesheets):
                    continue
                try:
                    stylesheets.append(stylesheet)
                    md5sum = hashlib.md5(open(stylesheet).read()).hexdigest()
                    tracelog.add_stylesheet(stylesheet, md5sum)
                except IOError, e:
                    pass

        tracelog.write(create_filename(self.trace_dir, "tracelog.xml"))
        print "Write Trace log '%s'" % (tracelog.filename)
        self.tracelog = tracelog

    def build_coverage_report(self, html_dir="", print_stats=False):
        cover = CoverAnalyzer()
        cover.fromlog(self.tracelog)
        if print_stats:
            cover.print_stats()
        if not(html_dir):
            html_dir = self.trace_dir
        cover.write_html(output_dir=html_dir)
        self.cover_report = cover

    def run(self, args):
        if not(self.command):
            return 0
        self._prepare_tracedir()
        rc = self.command.run(args, trace_dir=self.trace_dir)
        if rc != 0:
            self._remove_tracedir()
            return rc

        self._write_tracelog()

        if self.write_report:
            self.build_coverage_report()
        return rc


def create_filename(dirname, basename, max_files=1000, try_basename=True):
    if try_basename:
        filename_candidate = os.path.join(dirname, basename)
        if not(os.path.exists(filename_candidate)):
            return filename_candidate

    filename_candidate = ""
    corebasename, ext = os.path.splitext(basename)
    for i in range(1, max_files):
        filename_candidate = os.path.join(dirname,
                                          "%s-%04d%s" % (corebasename, i, ext))
        if not(os.path.exists(filename_candidate)):
            break
    return filename_candidate


def cmdline(command, parser=None, description='Run XSLT script with traces'):
    import os
    import sys

    parser = cmdline_parser(parser=parser, description=description)
    options, remain_args = parser.parse_known_args()
    cmdline_runargs(command, options, remain_args)


def cmdline_parser(parser=None, description=""):
    if not(parser):
        parser = ArgumentParser(description=description)
    parser.add_argument("--trace-dir",
          help="Directory containing the traces")
    parser.add_argument("--no-snapshot", action="store_false", dest="snapshot",
          default=True,
          help="Do not create a dated subdirectory containing the traces")
    parser.add_argument("--report", action="store_true",
          help="Build the HTML coverage report from the run")
    return parser


def cmdline_runargs(command, options, args):
    if not(options.trace_dir):
        options.trace_dir = os.getcwd()
    else:
        options.trace_dir = os.path.abspath(options.trace_dir)

    runner = CoverageRunner(command=command,
                            snapshot=options.snapshot,
                            trace_dir=options.trace_dir,
                            write_report=options.report)

    rc = runner.run(args)
    return rc, runner


def main():
    from runners.saxon import TraceSaxon
    cmdline(TraceSaxon())

if __name__ == "__main__":
    main()
