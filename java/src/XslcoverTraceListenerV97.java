/*
 * XSL Coverage - See COPYRIGHT
 * Traces for Saxon 9.x
 */
package xslcover.sf.saxon.trace;

import java.io.File;
import java.io.PrintStream;
import net.sf.saxon.lib.Logger;
import net.sf.saxon.lib.StandardLogger;
import net.sf.saxon.lib.TraceListener;
import net.sf.saxon.Controller;
import net.sf.saxon.expr.XPathContext;
import net.sf.saxon.om.Item;
import net.sf.saxon.om.StandardNames;
import net.sf.saxon.om.NodeInfo;
import net.sf.saxon.trace.InstructionInfo;
import net.sf.saxon.trace.LocationKind;
import net.sf.saxon.trace.XSLTTraceListener;

/**
 * Trace listener that writes XSL coverage info to a TRACE_FILE or to 
 * System.err otherwise. It extends the XSLTTraceListener to gain the
 * possibility to use -traceout:file to pass the trace file output
 */
public class XslcoverTraceListenerV97 extends XSLTTraceListener {

    private NodeInfo current_source;
    private Logger out = new StandardLogger();
    private boolean header_done = false;

    /**
     * Method called to supply the destination for output
     * @param stream a Logger to which any output produced by the
     * TraceListener should be written
     */
    public void setOutputDestination(Logger stream) {
        out = stream;
    }

    private void output_setup() {
        String outfile = System.getenv("TRACE_FILE");
        if (outfile != null) {
            try {
                out = new StandardLogger(new File(outfile));
            } catch (Exception e) {
                System.err.println("Invalid TRACE_FILE '" + outfile + "'");
            }
        }
    }

    /**
     * Called at start
     */
    public void open(Controller controller) {
        // Bug #3027: workaround to avoid duplicated root tag
        if (header_done) {
            return;
        }
        //output_setup();
        header_done = true;
        current_source = null;
        out.info("<trace time=\""
                + System.currentTimeMillis() + "\">");
    }

    /**
     * Called at end
     */
    public void close() {
        out.info("<end time=\"" + System.currentTimeMillis()
                + "\"/></trace>");
    }

    /**
     * Called when an instruction in the stylesheet gets processed
     */
    public void enter(InstructionInfo instruction, XPathContext context) {
        int loc = instruction.getConstructType();
        String tagname = tagName(loc);
        if (tagname != null) {
            Object val;
            String tag = "<stylesheet";
            String node = tagname; /* StandardNames.getLocalName(loc); */
            String file = instruction.getSystemId();
            if (file != null) {
                tag += " file=\"" + file + "\"";
            }
            tag += " element=\"" + node + "\"";
            String name = null;
            String match = null;
            String mode = null;
            if (instruction.getObjectName() != null) {
                name = instruction.getObjectName().getDisplayName();
            } else if (instruction.getProperty("name") != null) {
                name = instruction.getProperty("name").toString();
            }
            if (name != null) {
                tag += " name=\"" + name + "\"";
            }
            val = instruction.getProperty("match");
            if (val != null) {
                tag += " match=\"" + val.toString() + "\"";
            }
            val = instruction.getProperty("mode");
            if (val != null) {
                tag += " mode=\"" + val.toString() + "\"";
            }
            tag += " line=\"" + instruction.getLineNumber() + "\"";
            tag += " time=\"" + System.currentTimeMillis() + "\"";
            tag += ">";
            /*
            if (current_source != null) {
                tag += "<source ";
                tag += " file=\"" + current_source.getSystemId() + "\"";
                tag += " line=\"" + current_source.getLineNumber() + "\"";
                tag += " node=\"" + current_source.getLocalName() + "\"";
                tag += "/>";
            }
            */
            out.info(tag);
        } else {
            System.err.println("Unused instr: " + loc);
        }
    }

    /**
     * Called after an instruction of the stylesheet got processed
     */
    public void leave(InstructionInfo instruction) {
        int loc = instruction.getConstructType();
        String tagname = tagName(loc);
        if (tagname != null) {
            String tag = "<end time=\"" + System.currentTimeMillis()
                    + "\"/>";
            tag += "</stylesheet>";
            out.info(tag);
        }
    }

    /**
     * Method that is called by an instruction that changes the current item
     * in the source document: that is, xsl:for-each, xsl:apply-templates,
     * xsl:for-each-group.
     * The method is called after the enter method for the relevant
     * instruction, and is called once for each item processed.
     */
    /**
     * Called when a node of the source tree gets processed
     */
    public void startCurrentItem(Item currentItem) {
        String tag = "";
        if (currentItem instanceof NodeInfo) {
            current_source = (NodeInfo) currentItem;
            tag += "<source ";
            tag += " file=\"" + current_source.getSystemId() + "\"";
            tag += " line=\"" + current_source.getLineNumber() + "\"";
            tag += " node=\"" + current_source.getDisplayName() + "\"";
            tag += ">";
        }
        out.info(tag);
    }

    /**
     * Called when a node of the source tree got processed
     */
    public void endCurrentItem(Item currentItem) {
        if (currentItem instanceof NodeInfo) {
            String tag = "</source>";
            out.info(tag);
            current_source = null;
        }
    }

    /**
     * Get the output destination
     */
    public Logger getOutputDestination() {
        return out;
    }

    /*
    protected String tag(int construct) {
        return tagName(construct);
    }
    */

    public static String tagName(int construct) {
        if (construct < 1024) {
            return StandardNames.getDisplayName(construct);
        }
        switch (construct) {
            case LocationKind.LITERAL_RESULT_ELEMENT:
                return "LRE";
            case LocationKind.LITERAL_RESULT_ATTRIBUTE:
                return "ATTR";
            case LocationKind.LET_EXPRESSION:
                return "xsl:variable";
            case LocationKind.EXTENSION_INSTRUCTION:
                return "extension-instruction";
            case LocationKind.TRACE_CALL:
                return "user-trace";
            default:
                return null;
        }
    }
}

