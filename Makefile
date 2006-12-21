# PO = ca de es fr hr it pl pt pt_BR ro sv zh_CN

DESTDIR = ./tmp
APPNAME = gtkfilesplitter
PO = es

PREFIX ?= /usr

all: check po-data
	@echo "Done"
	@echo "Type: make install now"

check:
	@/bin/echo -n "Checking for Python... "
	@which python || ( echo "Not found." && /bin/false )
	@./check.py

clean:
	find . -type f -iregex '.*~$$'  -print | xargs rm -rf
	find . -type d -iregex '.*\.svn$$'  -print | xargs rm -rf
	find . -type f -iregex '.*\.pyc$$'  -print | xargs rm -rf
	find . -type f -iregex '.*\.gladep$$'  -print | xargs rm -rf
	find . -type f -iregex '.*\.bak$$'  -print | xargs rm -rf

make-install-dirs: make-install-dirs-po

	mkdir -p $(DESTDIR)$(PREFIX)/bin
	mkdir -p $(DESTDIR)$(PREFIX)/share/applications
	mkdir -p $(DESTDIR)$(PREFIX)/share/gtkfilesplitter
	mkdir -p $(DESTDIR)$(PREFIX)/share/pixmaps
	mkdir -p $(DESTDIR)$(PREFIX)/share/gnome/help/gtkfilesplitter/C
	mkdir -p $(DESTDIR)$(PREFIX)/share/locale

make-install-dirs-po:
	for lang in $(PO); do mkdir -p $(DESTDIR)$(PREFIX)/share/locale/$$lang/LC_MESSAGES; done

install: make-install-dirs install-po
	install -m 644 *.py $(DESTDIR)$(PREFIX)/share/gtkfilesplitter

	install -m 755 gtkfilesplitter.py $(DESTDIR)$(PREFIX)/share/gtkfilesplitter

	install -m 644 gtkfilesplitter.glade $(DESTDIR)$(PREFIX)/share/gtkfilesplitter
	install -m 644 gtkfilesplitter*.png $(DESTDIR)$(PREFIX)/share/gtkfilesplitter
	install -m 644 gtkfilesplitter.desktop $(DESTDIR)$(PREFIX)/share/applications/

	# sed 's/aptoncd.glade/\/usr\/share\/aptoncd\/aptoncd.glade/' $(DESTDIR)$(PREFIX)/share/aptoncd/config.py > $(DESTDIR)$(PREFIX)/share/aptoncd/config
	# sed 's/content.xml/\/usr\/share\/aptoncd\/content.xml/' $(DESTDIR)$(PREFIX)/share/aptoncd/config > $(DESTDIR)$(PREFIX)/share/aptoncd/config.py
	# sed 's/locale/\/usr\/share\/locale/' $(DESTDIR)$(PREFIX)/share/aptoncd/config.py > $(DESTDIR)$(PREFIX)/share/aptoncd/config
	# sed 's/doc\/C\/index.xml/\/usr\/share\/gnome\/help\/aptoncd\/C\/index.xml/' $(DESTDIR)$(PREFIX)/share/aptoncd/config > $(DESTDIR)$(PREFIX)/share/aptoncd/config.py
	# rm $(DESTDIR)$(PREFIX)/share/aptoncd/config 

	cd $(DESTDIR)$(PREFIX)/bin && \
	ln -sf ../share/aptoncd/gtkfilesplitter.py gtkfilesplitter && \
	chmod 755 gtkfilesplitter
		
install-po:
	for lang in $(PO); do install -m 644 locale/$$lang/LC_MESSAGES/* $(DESTDIR)$(PREFIX)/share/locale/$$lang/LC_MESSAGES/; done

po-dir:
	for lang in $(PO); do mkdir -p locale/$$lang/LC_MESSAGES/ ;done

po-data: po-dir
	for lang in $(PO); do msgfmt locale/$$lang.po -o locale/$$lang/LC_MESSAGES/gtkfilesplitter.mo;done

po-gen:
	intltool-extract --type=gettext/glade gtkfilesplitter.glade
	xgettext -k_ -kN_ -o locale/messages.pot *.py *.h
	for lang in $(PO); do msgmerge -U locale/$$lang.po locale/gtkfilesplitter.pot; done
