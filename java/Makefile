ifeq ($(SAXON_VERSION),6)

XSLCOVER_JAR = xslcover-saxon.jar
CLASS_DIR = lib/saxon6
SAXON_JAR = /usr/share/java/saxon.jar
SRC_FILES = src/XslcoverTraceListenerV65.java

else

XSLCOVER_JAR = xslcover-saxon9he.jar
CLASS_DIR = lib/saxon9
SAXON_JAR = /usr/share/java/saxon9he.jar
SRC_FILES = src/XslcoverTraceListenerV97.java

endif

all:
	$(MAKE) archive SAXON_VERSION=6
	$(MAKE) archive SAXON_VERSION=9

archive: $(XSLCOVER_JAR)

$(XSLCOVER_JAR): classes
	jar cvf $@ -C $(CLASS_DIR) .

classes: $(SRC_FILES)
	mkdir -p $(CLASS_DIR)
	javac -cp $(SAXON_JAR) -d $(CLASS_DIR) $<

