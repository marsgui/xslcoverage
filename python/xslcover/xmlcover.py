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

from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter


class Line:
    def __init__(self, fileobj, linenum, content=""):
        self.fileobj = fileobj
        self.linenum = linenum
        self.covered_fragments = []
        self.content = content

    def cover_fragment(self, fragment, source):
        self.covered_fragments.append((fragment, source))

    def __cmp__(self, other):
        return cmp(self.linenum, other.linenum)


class CoverFileData:
    def __init__(self, filepath=""):
        self.filepath = filepath
        self._trash_line = Line(self, -1)
        self.lines = {}
        if self.filepath:
            self.content = open(self.filepath).readlines()
        else:
            self.content = []

    def getline(self, linestr):
        try:
            linenum = int(linestr)
            lineobj = self.lines.get(linenum, None)
            if not(lineobj):
                lineobj = Line(self, linenum, self.content[linenum-1])
                self.lines[linenum] = lineobj
        except:
            lineobj = self._trash_line
        return lineobj


class Position:
    def __init__(self, bufpos, linepos):
        self.position(bufpos, linepos)

    def position(self, bufpos, linepos):
        self.bufpos = bufpos
        self.linepos = linepos

class ElementZone:
    def __init__(self, tag):
        self.start = Position(0,0)
        self.end = Position(0,0)
        self.tag = tag
        self.empty = False

class ElementList:
    def __init__(self):
        self.starting = []
        self.ending = []

class TreeLineBuilder:
    maxDepth = 0
    tag_pattern = "((\w+:)?(%s))"

    def __init__(self, databuf):
        self.tag_stack = []
        self.tag_zones = []
        self.tag_lines = {}
        self.databuf = databuf
        self.datapos = Position(0,1) # First line is '1'
        self.depth = 0

    def _abs_from(self, new_pos):
        abs_pos = self.datapos.bufpos + new_pos
        buf = self.databuf[self.datapos.bufpos:abs_pos]
        lines = buf.split("\n")
        #print lines, len(lines)
        abs_line = self.datapos.linepos + len(lines) -1
        return (abs_pos, abs_line)

    def _new_element(self, tag):
        e = ElementZone(tag)
        self.tag_stack.append(e)
        self.tag_zones.append(e)
        return e

    def _set_starting_line(self, e):
        l = self.tag_lines.get(e.start.linepos, ElementList())
        l.starting.append(e)
        self.tag_lines[e.start.linepos] = l

    def _set_ending_line(self, e):
        l = self.tag_lines.get(e.end.linepos, ElementList())
        l.ending.append(e)
        self.tag_lines[e.end.linepos] = l

    def _split_xmlns(self, tag):
        m = re.match("{([^}]+)}(.*)", tag)
        if m:
            return m.group(1), m.group(2)
        else:
            return "", tag

    def start(self, tag, attrib):   # Called for each opening tag.
        buf = self.databuf[self.datapos.bufpos:]

        xmlns, tag = self._split_xmlns(tag)

        m = re.search("<"+self.tag_pattern % tag, buf)
        if not(m):
            print "%s => '%s'" % (tag, buf)
        fulltag = m.group(1)
        abs_pos, abs_line = self._abs_from(m.start())
        #print "<%s>: %d L%d" % (fulltag, abs_pos, abs_line)
        e = self._new_element(fulltag)
        e.start.position(abs_pos, abs_line)
        self._set_starting_line(e)
        self.datapos.position(abs_pos, abs_line)
        self.depth += 1
        if self.depth > self.maxDepth:
            self.maxDepth = self.depth

    def end(self, tag):             # Called for each closing tag.
        buf = self.databuf[self.datapos.bufpos:]
        xmlns, tag = self._split_xmlns(tag)
        m1 = re.search("</"+self.tag_pattern % tag+"\s*>", buf)
        m2 = re.search("<"+self.tag_pattern % tag+"(\s.*?)?/>",
                          buf, re.M|re.DOTALL)
        if not(m1 and m2):
            m = m1 or m2
        elif m1.end() < m2.end():
            m = m1
        else:
            m = m2
        #if not(m):
        #    m = re.search("<"+self.tag_pattern % tag+"/>", buf)
        abs_pos, abs_line = self._abs_from(m.end())
        fulltag = m.group(1)
        #print "</%s>: %d L%d" % (fulltag, abs_pos, abs_line)
        e = self.tag_stack[-1]
        e.end.position(abs_pos, abs_line)
        if m == m2: e.empty = True
        self._set_ending_line(e)
        self.datapos.position(abs_pos, abs_line)
        self.depth -= 1
        self.tag_stack.remove(e)

    def data(self, data):
        pass
        #print '"%s"' % data

    def close(self):    # Called when all data has been parsed.
        #for e in self.tag_zones:
        #    print "<%s>: %d %d (%d %d)" % (e.tag,
        #                                   e.start.bufpos, e.end.bufpos,
        #                                   e.start.linepos, e.end.linepos)
        return self.maxDepth


class XmlCoverFile:
    def __init__(self, file_data):
        self.data = file_data
        self.xfilter = XmlFilter()
        self._compute_coverage()

    def line_status(self, linenum):
        if self.unused_lines.has_key(linenum):
            return "unused"
        elif self.data.lines.has_key(linenum):
            return "covered"
        else:
            return "uncovered"

    def content_string(self):
        return "".join(self.data.content)

    def filepath(self):
        return self.data.filepath

    def _complete_coverage(self):
        data = self.data
        comments = self.xfilter.filter_on_comment(data.content)
        for linenum in comments.keys():
            line = data.getline(linenum)
            line.cover_fragment("comment", None)
        blanks = self.xfilter.filter_on_empty(data.content)
        for linenum in blanks.keys():
            line = data.getline(linenum)
            line.cover_fragment("blank", None)
        declarations = self.xfilter.filter_on_declaration(data.content)
        for linenum in declarations.keys():
            line = data.getline(linenum)
            line.cover_fragment("declaration", None)

        self.unused_lines = comments
        self.unused_lines.update(blanks)
        self.unused_lines.update(declarations)

    def _fix_xsl_coverage(self):
        # print ">>>>", self.data.filepath
        data = self.content_string()
        tree_builder = TreeLineBuilder(data)
        parser = ET.XMLParser(target=tree_builder)
        parser.feed(data)
        parser.close()
        for linenum, elements in tree_builder.tag_lines.items():
            if not(elements.ending):
                continue
            if (elements.starting):
                continue
            if self.line_status(linenum) == "covered":
                for e in elements.ending:
                    if (e.empty and e.start.linepos < e.end.linepos):
                        for i in range(e.start.linepos, e.end.linepos):
                            if self.line_status(i) != "covered":
                                #print "LineS %d: should be covered too" % (i)
                                line_st = self.data.getline(i)
                                line_st.cover_fragment("empty filled", None)
                continue
            end_of_covered = [e for e in elements.ending \
                              if self.line_status(e.start.linepos) == "covered"]
            if len(end_of_covered) == len(elements.ending):
                #print "LineE %d: should be covered too" % (linenum)
                #line_st = self.data.getline(e.start.linepos)
                line_end = self.data.getline(linenum)
                line_end.cover_fragment("end keyword", None)

    def _compute_coverage(self):
        self._complete_coverage()
        self._fix_xsl_coverage()
        self.total_linecount = len(self.data.content)
        self.covered_linecount = len(self.data.lines.keys())
        self.unused_linecount = len(self.unused_lines.keys())
        self.payload_covered = self.covered_linecount - self.unused_linecount
        self.payload_total = self.total_linecount - self.unused_linecount

    def covering_files(self):
        covered_lines = self.data.lines.values()
        covered_lines.sort()
        for line in covered_lines:
            # Skip useless lines
            if self.unused_lines.has_key(line.linenum):
                continue
            files = {}
            for frag, source_line in line.covered_fragments:
                if not(source_line):
                    continue
                source = "%s:%d" % (source_line.fileobj.filepath,
                                    source_line.linenum)
                covered_frags = files.get(source, [])
                if not(frag in covered_frags):
                    covered_frags.append(frag)
                files[source] = covered_frags
            yield (line.linenum, files)

    def print_stats(self):
        print "Coverage of %s: %d/%d (%d/%d)" % (self.data.filepath,
               self.payload_covered, self.payload_total,
               self.covered_linecount, self.total_linecount)

        covered_lines = self.data.lines.values()
        covered_lines.sort()
        for line in covered_lines:
            # Skip useless lines
            if self.unused_lines.has_key(line.linenum):
                continue
            data = []
            for frag, source_line in line.covered_fragments:
                if frag in ("comment", "blank"):
                    data.append(frag)
                elif source_line:
                    data_line = "(%s)%s:%s" % \
                                (frag, source_line.fileobj.filepath,
                                           source_line.linenum)
                    if not(data_line in data):
                        data.append(data_line)
            txt_sources = "\n       ".join(textwrap.wrap(", ".join(data)))
            print "  %03d: %s" % (int(line.linenum), txt_sources)


class XmlFilter:
    COMMENT_LINE = 1
    EMPTY_LINE = 2
    DECL_LINE = 4

    def __init__(self, input_lines=None):
        self.content = input_lines or []

    def filter_on(self, filter_type, input_lines=None):
        content = input_lines or self.content
        lines = {}
        if (filter_type & self.EMPTY_LINE):
            lines.update(self.filter_on_empty(content))
        if (filter_type & self.COMMENT_LINE):
            lines.update(self.filter_on_comment(content))
        if (filter_type & self.DECL_LINE):
            lines.update(self.filter_on_declaration(self, content))
        return lines

    def filter_on_empty(self, content):
        filtered_lines = {}
        for i, line in enumerate(content):
            if not(line.strip()):
                filtered_lines[i+1] = line
        return filtered_lines

    def filter_on_comment(self, content):
        data = "".join(content)
        filtered_lines = {}
        string_stack = 0
        line_stack = 0
        for m in re.finditer("(<!--.*?-->)", data, re.MULTILINE|re.DOTALL):
            #print line_stack
            lines_before = data[string_stack:m.start()].split("\n")
            lines_comment = data[m.start():m.end()].split("\n")
            line_after = data[m.end():].split("\n", 1)[0]

            # The first line of the comment has things before
            if (lines_before[-1].strip()):
                lines_comment = lines_comment[1:]
            else:
                lines_before = lines_before[:-1]

            # The last line of the comment has things after
            if (line_after.strip()) and lines_comment:
                lines_comment = lines_comment[:-1]
                line_blank = ""
            else:
                line_blank = line_after+"\n"

            #print "before: %d (%s)" % (len(lines_before), lines_before)
            #print "comment: %d" % (len(lines_comment))
            #print "%d - %d: comment" % (line_stack+len(lines_before)+1,
            #                line_stack+len(lines_before)+len(lines_comment))

            # Just count plain lines of comment
            line_stack += len(lines_before)
            for i, line in enumerate(lines_comment):
                filtered_lines[line_stack + i + 1] = line

            # resynch to a line not fully a comment
            line_stack += len(lines_comment)
            string_stack = m.end() + len(line_blank)

        return filtered_lines

    def filter_on_declaration(self, content):
        data = "".join(content)
        filtered_lines = {}
        m = re.search("<xsl:stylesheet\s.*?>", data, re.MULTILINE|re.DOTALL)
        if (m):
            for i, line in enumerate(data[:m.end()].split("\n")):
                filtered_lines[i + 1] = line

        m = re.search("</xsl:stylesheet>", data)
        if (m):
            endline = len(data[:m.start()].split("\n"))
            filtered_lines[endline] = content[endline-1]
        return filtered_lines


class HtmlFormatterCoverage(HtmlFormatter):
    def wrap(self, source, outfile):
        return HtmlFormatter.wrap(self, self._wrap_coverage(source), outfile)

    def set_cover_handler(self, coverinfo):
        self.cover_handler = coverinfo

    def _wrap_coverage(self, inner):
        i = 0
        for t, line in inner:
            if t:
                i += 1
                cls = self.cover_handler.line_status(i)
                yield 1, '<span class="%s">%s</span>' % (cls, line)
            else:
                yield 0, line


class HtmlCoverageWriter:
    DOC_HEADER = '''\
    <!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01//EN"
       "http://www.w3.org/TR/html4/strict.dtd">

    <html>
    <head>
      <title>%(title)s</title>
      <meta http-equiv="content-type" content="text/html; charset=%(encoding)s">
      <link rel="stylesheet" href="%(cssfile)s" type="text/css">
      <link rel="stylesheet" href="%(csscover)s" type="text/css">
      %(script)s
    </head>
    <body %(body_attr)s>
    <h2>%(title)s</h2>
    '''
    DOC_FOOTER = '''\
    </body>
    </html>
    '''

    def __init__(self, cssdir="htdocs"):
        self.lexer = get_lexer_by_name("xslt")
        self.cssdir = os.path.join(os.path.dirname(__file__), cssdir)
        self.cssfile = "source.css"
        self.csscover = "cover.css"
        self.jscover = "tablecover.js"
        self.formatter = HtmlFormatterCoverage(linenos=True,
                          cssclass="source", cssfile=self.cssfile)
        self.formatter.encoding = "utf-8"
        self.covering_full_path = False
        self.summary = []
        self.covering_files = []
        self.output_dir = ""

    def _push_covering(self, covering_file):
        if not(covering_file in self.covering_files):
            self.covering_files.append(covering_file)

    def _filename_html(self, filename, subdir=""):
        filename = os.path.basename(filename)
        outname = os.path.join(self.output_dir, subdir, filename + ".html")
        return outname

    def write_covering(self):
        html_dir = os.path.join(self.output_dir, "source")
        if not(os.path.exists(html_dir)):
            os.mkdir(html_dir)
        for filename in self.covering_files:
            code = open(filename).read()
            formatter = HtmlFormatter(linenos=True,
                                      cssclass="source",
                                      cssfile=self.cssfile,
                                      noclobber_cssfile=True,
                                      lineanchors="line",
                                      full=True,
                                      title=os.path.basename(filename))
            formatter.encoding = "utf-8"
            outname = self._filename_html(filename, "source")
            outfile = open(outname, "w")
            highlight(code, self.lexer, formatter, outfile)
            outfile.close()

    def write_popups(self, coverfile):
        p = '<div class="popup-list">\n'
        for linenum, covering_files in coverfile.covering_files():
            p += '<span class="popuptext" id="pop-%d"><pre>' % (linenum)
            filenames = covering_files.keys()
            filenames.sort()
            for filename in filenames:
                frags = covering_files.get(filename)
                filepath, linenum = filename.split(":")
                self._push_covering(filepath)
                # Use a relative path to the XML source
                filepath =  "source/" + os.path.basename(filepath) + ".html"
                if not(self.covering_full_path):
                    filename = os.path.basename(filename)
                p += '<a href="%s#line-%s">%s</a> (%s)\n' % \
                     (filepath, linenum, filename, ", ".join(frags))
            p += '</pre></span>'
        p += '</div>\n'
        return p

    def write_file(self, coverfile, outfile, title=""):
        self.formatter.set_cover_handler(coverfile)
        code = coverfile.content_string()

        script = '<script type="text/javascript" src="covertable.js"></script>'
        header = self.DOC_HEADER % dict(cssfile=self.cssfile,
                                        csscover=self.csscover,
                                        encoding=self.formatter.encoding,
                                        script=script,
                                        body_attr='onload="fill_popups()"',
                                        title=title)
        footer = self.DOC_FOOTER

        popups = self.write_popups(coverfile)
        table = highlight(code, self.lexer, self.formatter)#, f)
        outfile.write(header + popups + table + footer)

    def write_chunk(self, coverfile):
        filename = os.path.basename(coverfile.filepath())
        coverage_pct = 100.*float(coverfile.payload_covered)/\
                        float(coverfile.payload_total)
        title = "%s coverage = %d/%d (%5.2f%%)" % \
                (filename, coverfile.payload_covered, coverfile.payload_total,
                 coverage_pct)
        
        self.summary.append(dict(href=filename+".html",
                                 filename=filename,
                                 covered=coverfile.payload_covered,
                                 total=coverfile.payload_total,
                                 pct=coverage_pct))

        output_file = self._filename_html(filename)
        print output_file
        outfile = open(output_file, "wb")
        self.write_file(coverfile, outfile, title=title)
        outfile.close()

    def write_index(self, tracelog):
        row = '<tr>'\
              '<td><a href="%(href)s">%(filename)s</a></td>'\
              '<td class="lcount">%(covered)4d / %(total)4d</td>'\
              '<td class="percent">%(pct)5.2f%%</td>'\
              '</tr>\n'
        table = '<table class="sortable">\n'
        table += '<thead><tr><th>File</th>\
                             <th>Covered / Total</th>\
                             <th>Rate</th></tr></thead><tbody>'
        for data in  self.summary:
            table += row % data
        table += '</tbody></table>'
        script = '<script type="text/javascript" src="sorttable.js"></script>'
        header = self.DOC_HEADER % dict(cssfile=self.cssfile,
                                        csscover=self.csscover,
                                        encoding="utf-8",
                                        script=script,
                                        body_attr="",
                                        title="Coverage Summary")
        footer = self.DOC_FOOTER

        body = ''
        if tracelog:
            if tracelog.command:
                body += '<h3>Command runned</h3>\n'
                body += '<pre>%s</pre>' % tracelog.command
            body += '<h3>Trace files used</h3>\n'
            body += '<table><tr><td><pre>\n'
            for trace_file in tracelog.trace_files:
                body += '%s\n' % trace_file
            body += '</tr></td></pre></table>\n'
            body += '<h3>Covered Files</h3>\n'
        body += table

        output_file = os.path.join(self.output_dir, "coverage_index.html")
        print output_file
        outfile = open(output_file, "wb")
        outfile.write(header + body + footer)
        outfile.close()
        # Copy the styles 
        for cssfile in glob.glob(os.path.join(self.cssdir, "*.*s*")):
            shutil.copy(cssfile, self.output_dir)

    def write(self, tracelog, coverage_list, output_dir=""):
        if output_dir: self.output_dir = output_dir
        for xcover in coverage_list:
            self.write_chunk(xcover)
        self.write_index(tracelog)
        self.write_covering()


class XslFile(CoverFileData):
    pass

class XmlFile(CoverFileData):
    pass

class FileManager:
    def __init__(self, file_type):
        self.file_type = file_type
        self.files = {}
        self._trash_file = file_type()

    def get_or_create(self, filepath):
        #print self.files, filepath
        _file = self.files.get(filepath, None)
        if not(_file):
            if os.path.isfile(filepath):
                _file = self.file_type(filepath)
                self.files[filepath] = _file
            else:
                _file = self._trash_file
        return _file

class TraceLog:
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
        self.xslfiles = FileManager(XslFile)
        self.xmlfiles = FileManager(XmlFile)
        self.html_writer = HtmlCoverageWriter()
        self.stats_done = False
        self.traces = []
        self.coverages = []
        self.tracelog = None

    def fromlog(self, tracelog):
        self.tracelog = tracelog
        for trace_file in tracelog.trace_files:
            self.read_trace(trace_file)

    def read_trace(self, xmlfilename):
        document = ET.parse(xmlfilename)
        self.traces.append(document)
        root = document.getroot()
        self._parse_children(root, None)

    def print_stats(self):
        self._do_stats()
        #print self.xslfiles.files
        for xcover in self.coverages:
            xcover.print_stats()

    def write_html(self, output_dir=""):
        self._do_stats()
        self.html_writer.write(self.tracelog, self.coverages, output_dir)

    def _do_stats(self):
        if not(self.stats_done):
            for xslfile in self.xslfiles.files.values():
                xcover = XmlCoverFile(xslfile)
                self.coverages.append(xcover)
            self.stats_done = True

    def _parse_children(self, node, source):
        for child in node:
            if child.tag == "stylesheet":
                #print source
                self._process_stylesheet(child, source)
            elif child.tag == "source":
                self._process_source(child)

    def _process_stylesheet(self, xslnode, source):
        xslfile = self.getxsl(xslnode.get("file").replace("file:",""))
        line = xslfile.getline(xslnode.get("line"))
        line.cover_fragment(xslnode.get("element"), source)
        self._parse_children(xslnode, source)

    def _process_source(self, xmlnode):
        xmlfile = self.getxml(xmlnode.get("file").replace("file:",""))
        source = xmlfile.getline(xmlnode.get("line"))
        self._parse_children(xmlnode, source)

    def getxsl(self, filename):
        return self.xslfiles.get_or_create(filename)

    def getxml(self, filename):
        return self.xmlfiles.get_or_create(filename)


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

