
SAXON_JAR = /usr/share/java/saxon.jar
CLASS_DIR = lib

xslcover.jar: classes
	jar cvf $@ -C $(CLASS_DIR) .

classes: src/TimedTraceListener.java
	mkdir -p $(CLASS_DIR)
	javac -cp $(SAXON_JAR) -d $(CLASS_DIR) $<

