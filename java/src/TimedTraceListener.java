/*
 * XSL Coverage - See COPYRIGHT
 *
 */
package xslcover.saxon.trace;

import java.io.PrintStream;
import com.icl.saxon.om.NodeInfo;
import com.icl.saxon.NodeHandler;
import com.icl.saxon.Context;
import com.icl.saxon.trace.TraceListener;

/**
 * Trace listener that writes XSL coverage info to a TRACE_FILE or to 
 * System.err otherwise
 */

public class TimedTraceListener implements TraceListener {

    private NodeInfo current_source;
    private PrintStream out = System.err;

    public void output_setup() {
        String outfile = System.getenv("TRACE_FILE");
        if (outfile != null) {
            try {
                out = new PrintStream(outfile);
            } catch (Exception e) {
                System.err.println("Invalid TRACE_FILE '" + outfile + "'");
            }
        }
    }

    /**
     * Called at start
     */
    public void open() {
        output_setup();
        current_source = null;
        out.println("<trace time=\""
                + System.currentTimeMillis() + "\">");
    }

    /**
     * Called at end
     */
    public void close() {
        out.println("<end time=\"" + System.currentTimeMillis()
                + "\"/></trace>");
    }

    /**
     * Called for all top level elements
     */
    public void toplevel(NodeInfo element) {
    }

    /**
     * Called when an instruction in the stylesheet gets processed
     */
    public void enter(NodeInfo instruction, Context context) {
        if (instruction.getNodeType() == NodeInfo.ELEMENT) {
            String tag = "<stylesheet";
            String node = instruction.getLocalName();
            String file = instruction.getSystemId();
            if (file != null) {
                tag += " file=\"" + file + "\"";
            }
            tag += " element=\"" + node + "\"";
            String name = null;
            String match = null;
            name = instruction.getAttributeValue(instruction.getBaseURI(),
                                                 "name");
            match = instruction.getAttributeValue(instruction.getBaseURI(),
                                                  "match");
            if (name != null) {
                tag += " name=\"" + name + "\"";
            }
            if (match != null) {
                tag += " match=\"" + match + "\"";
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
            out.println(tag);
        }
    }

    /**
     * Called after an instruction of the stylesheet got processed
     */
    public void leave(NodeInfo instruction, Context context) {
        if (instruction.getNodeType() == NodeInfo.ELEMENT) {
            String tag = "<end time=\"" + System.currentTimeMillis()
                    + "\"/>";
            tag += "</stylesheet>";
            out.println(tag);
        }
    }

    /**
     * Called when a node of the source tree gets processed
     */
    public void enterSource(NodeHandler handler,
                            Context context) {
        String tag = "";
        current_source = context.getContextNodeInfo();
        if (current_source != null) {
            String mode = getModeName(context);
            tag += "<source ";
            tag += " file=\"" + current_source.getSystemId() + "\"";
            tag += " line=\"" + current_source.getLineNumber() + "\"";
            tag += " node=\"" + current_source.getLocalName() + "\"";
            if (mode.length() != 0) {
              tag += " mode=\"" + mode + "\"";
            }
            tag += ">";
        }
        out.println(tag);
    }

    /**
     * Called when a node of the source tree got processed
     */
    public void leaveSource(NodeHandler handler,
                            Context context) {
        String tag = "</source>";
        out.println(tag);
        current_source = null;
    }

    String getModeName(Context context) {
        int name_code = context.getMode().getNameCode();
        if (name_code == -1) {
            return "";
        } else {
            return
            context.getController().getNamePool().getDisplayName(name_code);
        }
    }

    /**
     * Set the output destination (default is System.err)
     * @param stream the output destination for tracing output
     */
    public void setOutputDestination(PrintStream stream) {
        out = stream;
    }

    /**
     * Get the output destination
     */
    public PrintStream getOutputDestination() {
        return out;
    }
}

