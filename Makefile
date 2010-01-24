
PREFIX=/usr/local
BINDIR=$(PREFIX)/bin
MANDIR=$(PREFIX)/share/man

CFLAGS=-Wall -Werror


all: ftpsync.1

.PHONY: all install clean

ftpsync.1: manual.t2t
	txt2tags -t man -i $^ -o $@

README.textile: manual.t2t
	txt2tags -t html -H -i $^ -o $@
	sed -i -e 's@<B>@**@g' -e 's@</B>@**@g' $@

clean:
	rm -f ftpsync.1

install: ftpsync.1
	mkdir -p $(BINDIR)
	install ftpsync $(BINDIR)/ftpsync
	mkdir -p $(MANDIR)/man1
	install ftpsync.1 $(MANDIR)/man1/ftpsync.1

