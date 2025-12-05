#
# cct instrumentation - LLVM instrumentation
# -----------------------------------------
#
# LLVM integration design comes wcventure.
#
# Copyright 2020, 2021 wcventure LLC All rights reserved.
#

BASE_DIR		:= $(shell pwd)

PREFIX      ?= ./build

VERSION     = $(shell grep '^\#define VERSION ' src/config.h | cut -d '"' -f2)

LLVM_CONFIG ?= llvm-config
GXX         ?= g++

CFLAGS      ?= -O3 -funroll-loops -I$(BASE_DIR)/include
CFLAGS      += -Wall -D_GNU_SOURCE -D_FORTIFY_SOURCE=2 -g -Wno-pointer-sign \
               -DVERI_LIB_PATH=\"$(HELPER_PATH)\" -DBIN_PATH=\"$(BIN_PATH)\" \
               -DVERSION=\"$(VERSION)\" -Wno-unused-but-set-variable \
               -Wno-unused-command-line-argument -Wno-unknown-warning-option -Wno-trigraphs -Wno-keyword-macro -Wno-sign-compare -Wno-pedantic -Wno-unused-variable

CXXFLAGS    ?= -O3 -funroll-loops -I$(BASE_DIR)/include
CLANGFLAGS  += -stdlib=libstdc++ -std=c++11 -Wno-keyword-macro -Wno-unknown-warning-option -Wno-unused-command-line-argument
CXXFLAGS    += -Wall -D_GNU_SOURCE -D_FORTIFY_SOURCE=2 -g -Wno-pointer-sign -Wno-writable-strings\
               -DVERSION=\"$(VERSION)\" -Wno-variadic-macros -Wno-unused-but-set-variable \
               -Wno-trigraphs -Wno-missing-braces -Wno-sign-compare -Wno-pedantic -Wno-unknown-warning-option -Wno-unused-variable
ASANFLAGS	=
ifdef ASAN
  ASANFLAGS	= -fsanitize=address
endif

ifdef VERI_TRACE_PC
  CFLAGS    += -DUSE_TRACE_PC=1
endif

ifdef LLVM362
  CFLAGS    += -D_GLIBCXX_USE_CXX11_ABI=0
  CXXFLAGS  += -D_GLIBCXX_USE_CXX11_ABI=0
endif

# Mark nodelete to work around unload bug in upstream LLVM 5.0+
CLANG_CFL    = `$(LLVM_CONFIG) --cxxflags` -Wl,-znodelete -fno-rtti -fpic $(CXXFLAGS)
CLANG_LFL    = `$(LLVM_CONFIG) --ldflags` $(LDFLAGS)

ifeq "$(shell uname)" "Darwin"
  CLANG_CFL    = -fno-exceptions -fno-rtti -D_GNU_SOURCE -D__STDC_CONSTANT_MACROS -D__STDC_FORMAT_MACROS -D__STDC_LIMIT_MACROS -fpic $(CXXFLAGS)
  CLANG_LFL    = $(LDFLAGS)
  CFLAGS      += -Wno-c++11-extensions #-L/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk/usr/lib 
  CXXFLAGS    += -Wno-c++11-extensions #-L/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk/usr/lib
endif

# User teor2345 reports that this is required to make things work on MacOS X.

ifeq "$(shell uname)" "Darwin"
  CLANG_LFL += -Wl,-flat_namespace -Wl,-undefined,suppress
endif

# We were using llvm-config --bindir to get the location of clang, but
# this seems to be busted on some distros, so using the one in $PATH is
# probably better.

ifeq "$(origin CC)" "default"
  CC         = clang
  CXX        = clang++
endif

ifndef VERI_TRACE_PC
  PROGS      = build/lib/veri-llvm-pass.so #build/obj/PFunc.o
else
  PROGS      = #build/obj/PFunc.o
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
build/lib/veri-llvm-pass.so: src/veri-llvm-pass.so.cc | test_deps
	$(CXX) $(CLANG_CFL) -Wno-deprecated -Wno-unused-command-line-argument -c $(GTESTDEF) $< -o build/lib/veri-llvm-pass.o $(CLANG_LFL)
	$(CXX) build/lib/veri-llvm-pass.o -dynamiclib -lc++ -lSystem -L `/usr/bin/xcrun --show-sdk-path -sdk macosx`/usr/lib -o $@
else
build/lib/veri-llvm-pass.so: src/veri-llvm-pass.so.cc | test_deps
	$(CXX) $(CLANG_CFL) -Wno-deprecated -shared $(GTESTDEF) $< -o $@ $(CLANG_LFL)
endif


.NOTPARALLEL: clean

clean:
	rm -f *.a *.o *.so *~ a.out core core.[1-9][0-9]*
	rm -f build/lib/*.o build/lib/*.so build/lib/*.dylib

install:
	@echo "begin install "$(PREFIX)
ifndef VERI_TRACE_PC
	cp build/lib/veri-llvm-pass.so $(PREFIX)/lib/
endif
	@echo $(PREFIX) "install success!"
