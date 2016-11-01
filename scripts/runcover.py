#!/usr/bin/env python
import os
import glob
import xml.etree.ElementTree as ET
import hashlib
from subprocess import Popen
from argparse import ArgumentParser
from xmlcover import CoverAnalyzer, TraceLog

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

def build_coverage_report(tracelog, html_dir, print_stats=False):
    cover = CoverAnalyzer()
    cover.fromlog(tracelog)
    if print_stats:
        cover.print_stats()
    cover.write_html(output_dir=html_dir)

def build_tracelog(cmd, trace_dir, old_files):
    # Find out the files newly written
    trace_files = glob.glob(os.path.join(trace_dir, "*.xml"))
    for old_file in old_files:
        if old_file in trace_files:
            trace_files.remove(old_file)

    tracelog = TraceLog()
    tracelog.set_command(" ".join(cmd))
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

    tracelog.write(create_filename(trace_dir, "tracelog.xml"))
    return tracelog

def cmdline_parser(description='Run script and handle traces'):
    parser = ArgumentParser(description=description)
    parser.add_argument("--trace-dir",
          help="Directory containing the traces")
    parser.add_argument("--no-snapshot", action="store_false", dest="snapshot",
          default=True,
          help="Do not create a dated subdirectory containing the traces")
    parser.add_argument("--report", action="store_true",
          help="Build the HTML coverage report from the run")
    return parser


def main():
    import os
    import sys
    from datetime import datetime

    parser = cmdline_parser(description='Run dblatex with traces')
    parser.add_argument("--script", help="Script to call")
    options, remain_args =  parser.parse_known_args()

    if not(options.script):
        options.script = "dblatex"

    if not(options.trace_dir):
        options.trace_dir = os.getcwd()
    else:
        options.trace_dir = os.path.abspath(options.trace_dir)

    if (options.snapshot):
        now = datetime.now()
        snapdir = now.strftime("%y%j%H%M%S")
        options.trace_dir = os.path.join(options.trace_dir, snapdir)
        os.mkdir(options.trace_dir)
        old_files = []
    else:
        old_files = glob.glob(os.path.join(options.trace_dir, "*"))
    
    s = TraceDblatex(options.script)
    s.run(remain_args, options.trace_dir)
    tracelog = build_tracelog(s.cmd, options.trace_dir, old_files)
    print "Write Trace log '%s'" % (tracelog.filename)

    if options.report:
        html_dir = options.trace_dir
        build_coverage_report(tracelog, html_dir)


if __name__ == "__main__":
    main()
