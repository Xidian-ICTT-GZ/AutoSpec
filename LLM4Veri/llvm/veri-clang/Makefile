#
# cct instrumentation - LLVM instrumentation
# -----------------------------------------
#
# LLVM integration design comes wcventure.
#
# Copyright 2020, 2021 wcventure LLC All rights reserved.
#

BASE_DIR		:= $(shell pwd)

PREFIX      ?= ./

VERSION     = $(shell grep '^\#define VERSION ' src/config.h | cut -d '"' -f2)

LLVM_CONFIG ?= llvm-config

CFLAGS      ?= -O0 -funroll-loops -I$(BASE_DIR)/../include
CFLAGS      += -Wall -D_GNU_SOURCE -D_FORTIFY_SOURCE=2 -g -Wno-pointer-sign \
               -DVERI_LIB_PATH=\"$(HELPER_PATH)\" -DBIN_PATH=\"$(BIN_PATH)\" \
               -DVERSION=\"$(VERSION)\" -Wno-unused-but-set-variable \
               -Wno-unused-command-line-argument -Wno-unknown-warning-option -Wno-trigraphs -Wno-keyword-macro -Wno-sign-compare -Wno-pedantic -Wno-unused-variable
ifdef VERI_TRACE_PC
  CFLAGS    += -DUSE_TRACE_PC=1
endif

CXXFLAGS    ?= -O0 -funroll-loops -I$(BASE_DIR)/../include
#CXXFLAGS    += -stdlib=libstdc++ -std=c++14
CXXFLAGS    += -Wall -D_GNU_SOURCE -D_FORTIFY_SOURCE=2 -g -Wno-pointer-sign \
               -DVERSION=\"$(VERSION)\" -Wno-variadic-macros -Wno-unused-but-set-variable \
               -Wno-unused-command-line-argument -Wno-unknown-warning-option -Wno-trigraphs -Wno-missing-braces -Wno-keyword-macro -Wno-sign-compare -Wno-pedantic -Wno-unused-variable
ASANFLAGS	=
ifdef ASAN
  ASANFLAGS	= -fsanitize=address
endif

# Mark nodelete to work around unload bug in upstream LLVM 5.0+
CLANG_CFL    = `$(LLVM_CONFIG) --cxxflags` -Wl,-znodelete -fno-rtti -fpic $(CXXFLAGS)
CLANG_LFL    = `$(LLVM_CONFIG) --ldflags` $(LDFLAGS)
LDL_FLAGS    = -ldl

ifeq "$(shell uname)" "Darwin"
  CLANG_CFL    = -fno-exceptions -fno-rtti -D_GNU_SOURCE -D__STDC_CONSTANT_MACROS -D__STDC_FORMAT_MACROS -D__STDC_LIMIT_MACROS -fpic $(CXXFLAGS)
  CLANG_LFL    = $(LDFLAGS)
  CFLAGS      += -Wno-c++11-extensions #-L/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk/usr/lib 
  CXXFLAGS    += -Wno-c++11-extensions -std=c++14 #-L/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk/usr/lib 
endif

# User teor2345 reports that this is required to make things work on MacOS X.

ifeq "$(shell uname)" "Darwin"
  CLANG_LFL += -Wl,-flat_namespace -Wl,-undefined,suppres
  LDL_FLAGS = 
endif

# We were using llvm-config --bindir to get the location of clang, but
# this seems to be busted on some distros, so using the one in $PATH is
# probably better.

ifeq "$(origin CC)" "default"
  CC         = clang
  CXX        = clang++
endif

ifndef VERI_TRACE_PC
  PROGS      = ./veri-clang
else
  PROGS      = ./veri-clang
endif

all: test_deps $(PROGS)

test_deps:
ifeq "$(shell uname)" "Darwin"
	@echo "[*] Skip checking for working 'llvm-config' on MacOS ..."
else
  ifndef VERI_TRACE_PC
	@echo "[*] Checking for working 'llvm-config'..."
	@which $(LLVM_CONFIG) >/dev/null 2>&1 || ( echo "[-] Oops, can't find 'llvm-config'. Install clang or set \$$LLVM_CONFIG or \$$PATH beforehand."; echo "    (Sometimes, the binary will be named llvm-config-3.5 or something like that.)"; exit 1 )
  else
	@echo "[!] Note: using -fsanitize=trace-pc mode (this will fail with older LLVM)."
  endif
endif
	@echo "[*] Checking for working '$(CC)'..."
	@which $(CC) >/dev/null 2>&1 || ( echo "[-] Oops, can't find '$(CC)'. Make sure that it's in your \$$PATH (or set \$$CC and \$$CXX)."; exit 1 )
	@echo "[+] All set and ready to build."

ifeq "$(shell uname)" "Darwin"
./veri-clang: src/veri-clang.c | test_deps
	$(CC) $(CFLAGS) -c $< -o $@.o $(LDFLAGS)
	ld $@.o -lSystem -L `/usr/bin/xcrun --show-sdk-path -sdk macosx`/usr/lib -o $@
	ln -sf veri-clang ./veri-clang++
else
./veri-clang: src/veri-clang.c | test_deps
	$(CC) $(CFLAGS) $< -o $@ $(LDFLAGS)
	ln -sf veri-clang ./veri-clang++
endif

test_build: $(PROGS)
	@echo "[*] Testing the CXX wrapper and instrumentation output..."
	unset VERI_USE_ASAN VERI_USE_MSAN VERI_INST_RATIO; VERI_QUIET=1 VERI_LIB_PATH=../ VERI_CC=$(CC) ./veri-clang $(CFLAGS) -Wno-return-type -c ./test/test.c -o ./test/bin/test.o $(LDFLAGS) $(ASANFLAGS)
	VERI_LIB_PATH=../ VERI_CXX=$(CXX) ./veri-clang++ ./test/bin/test.o -g -O0 -o ./test/bin/test $(LDL_FLAGS) -pthread $(ASANFLAGS)
	@echo "[+] All right, the instrumentation seems to be working!"

all_done: test_build
	@echo "[+] All done! You can now use '../veri-clang' to compile programs."

.NOTPARALLEL: clean

clean:
	rm -f *.a *.o *.so *~ a.out core core.[1-9][0-9]* ./test/bin/test
	rm -f $(PROGS) ./veri-clang++

install:
	@echo "begin install "$(PREFIX)
	cp ./veri-clang $(PREFIX)/bin/
	ln -sf veri-clang $(PREFIX)/bin/veri-clang++
	@echo $(PREFIX) "install success!"
