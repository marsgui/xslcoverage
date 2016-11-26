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
import runner
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
        self.trace_generator = ""

    def set_command(self, command):
        self.command = command

    def set_generator(self, trace_generator):
        self.trace_generator = trace_generator

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
        f.write("<trace-files")
        if self.trace_generator:
            f.write(' trace-generator="%s"' % self.trace_generator)
        f.write(">\n")
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
            self.trace_generator = node.get("trace-generator") or ""
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
        self.trace_parser_default = SaxonParser()
        self.html_writer = HtmlCoverageWriter()
        self.stats_done = False
        self.coverages = []
        self.tracelog = None

    def get_parser(self, trace_generator):
        parser = self.trace_parser_default
        if not(trace_generator):
            return parser
        try:
            parser = runner.load_parser(trace_generator)
        except Exception, e:
            print >> sys.stderr, "Cannot find parser: %s" % e
        return parser

    def fromlog(self, tracelog):
        self.tracelog = tracelog
        parser = self.get_parser(tracelog.trace_generator)
        for trace_file in tracelog.trace_files:
            parser.read_trace(trace_file)
        self.coverages = parser.get_coverages()

    def print_stats(self):
        title = "%30s %10s %6s %10s %6s" % \
                ("FILE", "PCOV / PTOT", "%PCOV", "LCOV / LTOT", "%LCOV")
        pattern = "%(filename)30s "
        pattern += "%(payload_covered)4d / %(payload_total)4d "
        pattern += "%(payload_pct)6.2f "
        pattern += "%(covered_linecount)4d / %(total_linecount)4d "
        pattern += "%(linecount_pct)6.2f"
        def sort_filename(o): return o.filepath()
        def sort_coverage_pct(o):
            return 100.*float(o.payload_covered)/o.payload_total
        coverages = reversed(sorted(self.coverages, key=sort_coverage_pct))

        print title
        for xcover in coverages:
            stats = xcover.get_stats()
            pc, pt = stats.get("payload_covered"), stats.get("payload_total")
            lc, lt = stats.get("covered_linecount"),stats.get("total_linecount")
            stats["filename"] = os.path.basename(xcover.filepath())
            stats["payload_pct"] = 100.*float(pc)/pt
            stats["linecount_pct"] = 100.*float(lc)/lt
            print pattern % stats

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

