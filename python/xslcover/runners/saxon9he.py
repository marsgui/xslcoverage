#
# XSL Coverage - See COPYRIGHT
#
import os
from xslcover import config 
from subprocess import Popen

def create_trace_filename(dirname, max_files=1000):
    filename_candidate = ""
    for i in range(1, max_files):
        filename_candidate = os.path.join(dirname, "trace-%04d.xml" % i)
        if not(os.path.exists(filename_candidate)):
            break
    return filename_candidate

class TraceSaxon9he:
    """
    Extend the default saxon script to have:
    - Catalog resolver (xml-resolver required)
    - XInclude support (xercesImpl required)
    - Tracing of data to compute coverage (xslcover required)
    """
    _classpath = ":".join(["%(saxon_path)s/saxon9he.jar",
                           "%(xml_resolver_path)s/xml-resolver.jar",
                           "/etc/xml/resolver",
                           "%(xerces_path)s/xercesImpl.jar",
                           "%(xslcover_path)s/xslcover-saxon9he.jar"])

    def __init__(self):
        java_paths = {}
        for path_key in ("saxon_path", "xml_resolver_path", "xerces_path",
                         "xslcover_path"):
            java_paths[path_key] = config.get_value(path_key, "/usr/share/java")
        self.classpath = self._classpath % java_paths

        self.cmd = ["java", "-classpath", self.classpath,
           "-Dorg.apache.xerces.xni.parser.XMLParserConfiguration=org.apache.xerces.parsers.XIncludeParserConfiguration",
           "net.sf.saxon.Transform",
           "-T:xslcover.sf.saxon.trace.XslcoverTraceListenerV97",
           "-x:org.apache.xml.resolver.tools.ResolvingXMLReader",
           "-y:org.apache.xml.resolver.tools.ResolvingXMLReader",
           "-r:org.apache.xml.resolver.tools.CatalogResolver"]

    def run(self, args, trace_dir="", trace_filename=""):
        if not(trace_filename):
            trace_filename = create_trace_filename(trace_dir)

        # With saxon 9 we can set the output trace file directly
        if trace_filename:
            print "Trace file set to %s" % trace_filename
            self.cmd.append("-traceout:%s" % trace_filename)

        p = Popen(self.cmd + args)
        rc = p.wait()
        return rc


class TraceRunner(TraceSaxon9he):
    "Plugin Class to load"



