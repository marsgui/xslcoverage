import os
import glob
import shutil
import textwrap
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter


class HtmlFormatterCoverage(HtmlFormatter):
    """
    Customize the pygments HTML formatter to add 'covered' or 'uncovered'
    class to the source code lines, so that it can be displayed differently
    through CSS styles.
    """
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
    """
    Main class in charge to build the whole report made of one HTML file per
    XSL Stylessheet covered, and a global coverage index.
    """
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
                cmd = textwrap.fill(tracelog.command, width=90,
                                break_long_words=False, break_on_hyphens=False)
                body += '<h3>Command runned</h3>\n'
                body += '<pre>%s</pre>' % cmd
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

