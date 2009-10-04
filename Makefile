
DESTDIR=/usr/local
BINDIR=$(DESTDIR)/bin

CFLAGS=-Wall -Werror


all: ftpsync.1

.PHONY: all install clean

ftpsync.1: manual.t2t
	txt2tags -t man -i $^ -o $@

README.textile: manual.t2t
	txt2tags -t textile -H -i $^ -o $@

clean:
	rm -f ftpsync.1

install:
	mkdir -p $(BINDIR)
	install ftpsync $(BINDIR)/ftpsync

