#
# XSL Coverage - See COPYRIGHT
#
import os
import config
from subprocess import Popen

class TraceSaxon:
    """
    Extend the default saxon script to have:
    - Catalog resolver (xml-resolver required)
    - XInclude support (xercesImpl required)
    - Tracing of data to compute coverage (xslcover required)
    """
    _classpath = ":".join(["%(saxon_path)s/saxon.jar",
                           "%(xml_resolver_path)s/xml-resolver.jar",
                           "/etc/xml/resolver",
                           "%(xerces_path)s/xercesImpl.jar",
                           "%(xslcover_path)s/xslcover.jar"])

    def __init__(self):
        java_paths = {}
        for path_key in ("saxon_path", "xml_resolver_path", "xerces_path",
                         "xslcover_path"):
            java_paths[path_key] = config.get_value(path_key, "/usr/share/java")
        self.classpath = self._classpath % java_paths

        self.cmd = ["java", "-classpath", self.classpath,
           "-Dorg.apache.xerces.xni.parser.XMLParserConfiguration=org.apache.xerces.parsers.XIncludeParserConfiguration",
           "com.icl.saxon.StyleSheet",
           "-TL", "dblatex.saxon.trace.TimedTraceListener",
           "-x", "org.apache.xml.resolver.tools.ResolvingXMLReader",
           "-y", "org.apache.xml.resolver.tools.ResolvingXMLReader",
           "-r", "org.apache.xml.resolver.tools.CatalogResolver"]

    def run(self, args, trace_dir="", trace_filename=""):
        if not(trace_filename):
            trace_filename = create_trace_filename(trace_dir)

        if trace_filename:
            print "Write traces to %s" % trace_filename
            env = {}
            env.update(os.environ)
            env.update({ "TRACE_FILE": trace_filename })
        else:
            env = None

        p = Popen(self.cmd + args, env=env)
        rc = p.wait()
        return rc


def create_trace_filename(dirname, max_files=1000):
    filename_candidate = ""
    for i in range(1, max_files):
        filename_candidate = os.path.join(dirname, "trace-%04d.xml" % i)
        if not(os.path.exists(filename_candidate)):
            break
    return filename_candidate


def main():
    import sys
    from argparse import ArgumentParser
    parser = ArgumentParser(description='XSLT engine with traces')
    parser.add_argument("-D", "--trace-dir", default="",
          help="Directory containing the traces")

    options, remain_args =  parser.parse_known_args()

    if not(options.trace_dir):
        options.trace_dir = os.environ.get("TRACE_DIRECTORY", "")

    s = TraceSaxon()
    rc = s.run(remain_args, trace_dir=options.trace_dir)
    sys.exit(rc)
 

if __name__ == "__main__":
    main()