#
# XSL Coverage - See COPYRIGHT
#
import os
import sys
import re
import textwrap
import shutil
import glob
import xml.etree.ElementTree as ET
from htmlreport import HtmlCoverageWriter
from saxontrace import SaxonParser


class TraceLog:
    """
    Trace summary: lists the data produced (trace files) or involved in
    producing the traces (XSL files, command runned) and context. 
    """
    def __init__(self):
        self.stylesheets = []
        self.trace_files = []
        self.md5sum = {}
        self.command = ""
        self.filename = ""
        self.root_tag = "trace-report"

    def set_command(self, command):
        self.command = command

    def add_trace(self, trace_file):
        self.trace_files.append(trace_file)

    def set_traces(self, trace_files):
        self.trace_files = [] + trace_files

    def add_stylesheet(self, stylesheet, md5sum=""):
        if (stylesheet in self.stylesheets):
            return
        self.stylesheets.append(stylesheet)
        self.md5sum[stylesheet] = md5sum

    def write(self, tracelog):
        self.filename = tracelog
        f = open(tracelog, "w")
        f.write("<%s>\n" % self.root_tag)
        f.write("<command>%s</command>\n" % self.command)
        f.write("<trace-files>\n")
        for trace_file in self.trace_files:
            f.write('<file path="%s"/>\n' % os.path.abspath(trace_file))
        f.write("</trace-files>\n")
        f.write("<stylesheets>\n")
        for stylesheet in self.stylesheets:
            md5sum = self.md5sum.get(stylesheet, "")
            f.write('<file path="%s" md5sum="%s"/>\n' % (stylesheet, md5sum))
        f.write("</stylesheets>\n")
        f.write("</%s>\n" % self.root_tag)
        f.close()

    def fromfile(self, tracelog):
        self.filename = tracelog
        tree = ET.parse(self.filename)
        root = tree.getroot()
        if root.tag != self.root_tag:
            return
        node = root.find("command")
        if not(node is None):
            self.set_command(node.text)
        node = root.find("trace-files")
        if not(node is None):
            for trace_file in node.findall("file"):
                self.add_trace(trace_file.get("path"))
        node = root.find("stylesheets")
        if not(node is None):
            for trace_file in node.findall("file"):
                self.add_stylesheet(trace_file.get("path"),
                                    trace_file.get("md5sum"))

    def check_consistency(self):
        pass


class CoverAnalyzer:
    def __init__(self):
        self.trace_parser = SaxonParser()
        self.html_writer = HtmlCoverageWriter()
        self.stats_done = False
        self.coverages = []
        self.tracelog = None

    def fromlog(self, tracelog):
        self.tracelog = tracelog
        for trace_file in tracelog.trace_files:
            self.trace_parser.read_trace(trace_file)
        self.coverages = self.trace_parser.get_coverages()

    def print_stats(self):
        for xcover in self.coverages:
            xcover.print_stats()

    def write_html(self, output_dir=""):
        self.html_writer.write(self.tracelog, self.coverages, output_dir)


def cmdline_runargs(options, args, parser=None):
    tracelog = TraceLog()
    if options.from_log:
        tracelog.fromfile(options.from_log)
    else:
        # Build a partial trace context
        trace_files = args
        if options.trace_dir:
            trace_files += glob.glob(os.path.join(options.trace_dir, "*.xml"))
        tracelog.set_traces(trace_files)

    if options.html_dir:
        output_dir = options.html_dir
    elif options.from_log:
        output_dir = os.path.dirname(os.path.abspath(options.from_log))
    elif options.trace_dir:
        output_dir = options.trace_dir
    else:
        output_dir = ""

    if len(tracelog.trace_files) == 0:
        print >> sys.stderr, "Missing trace file to process"
        if parser: parser.parse_args(["-h"])
        else: return

    cover = CoverAnalyzer()
    cover.fromlog(tracelog)
    if options.show_stats:
        cover.print_stats()
    cover.write_html(output_dir=output_dir)
 

def main():
    import sys
    import glob
    from optparse import OptionParser
    parser = OptionParser(usage="%s [options] [trace1...]" % sys.argv[0])
    parser.add_option("-f", "--from-log",
                      help="Trace report of the traces")
    parser.add_option("-r", "--trace-dir",
                      help="Directory containing the traces")
    parser.add_option("-s", "--show-stats", action="store_true",
                      help="Show coverage statistics on console")
    parser.add_option("-O", "--html-dir",
                      help="Directory containing the HTML output")

    (options, args) = parser.parse_args()
    cmdline_runargs(options, args)


if __name__ == "__main__":
    main()

