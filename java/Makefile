
SAXON_JAR = /usr/share/java/saxon.jar
CLASS_DIR = lib

xslcover.jar: classes
	jar cvf $@ -C lib .

classes: src/TimedTraceListener.java
	javac -cp $(SAXON_JAR) -d $(CLASS_DIR) $<

