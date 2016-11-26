#
# XSL Coverage - See COPYRIGHT
#
import re
from coverapi import XmlCoverFileBase


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


class XmlCoverFile(XmlCoverFileBase):
    """
    Core class containing the coverage data related to an XSL file
    """
    def __init__(self, file_data):
        self.data = file_data
        self.xfilter = XmlFilter()
        self.unused_lines = {}
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

    def fix_coverage(self):
        pass

    def _compute_coverage(self):
        self._complete_coverage()
        self.fix_coverage()
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

    def get_stats(self):
        return dict(payload_covered=self.payload_covered,
                    payload_total=self.payload_total,
                    covered_linecount=self.covered_linecount,
                    total_linecount=self.total_linecount)

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


