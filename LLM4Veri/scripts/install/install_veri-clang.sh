#!/bin/bash

# For Mac
if [ $(command uname) == "Darwin" ]; then
	if ! [ -x "$(command -v greadlink)"  ]; then
		brew install coreutils
	fi
	BIN_PATH=$(greadlink -f "$0")
	ROOT_DIR=$(dirname $(dirname $(dirname $(dirname $BIN_PATH))))
# For Linux
else
	BIN_PATH=$(readlink -f "$0")
	ROOT_DIR=$(dirname $(dirname $(dirname $(dirname $BIN_PATH))))
fi

set -euxo pipefail

# For Mac
if [ $(command uname) == "Darwin" ]; then
    if ! [ -d "${ROOT_DIR}/clang+llvm"  ]; then
        ${ROOT_DIR}/LLM4Veri/scripts/requires/get_llvm.sh
    fi
	BOOST_PATH=$(find /usr/local/Cellar/boost -name "include" -type d -print0)
	BOOST_PATH=${BOOST_PATH//include\/usr/include:\/usr}
	export C_INCLUDE_PATH=${C_INCLUDE_PATH}:${BOOST_PATH}
	export CPLUS_INCLUDE_PATH=${CPLUS_INCLUDE_PATH}:${BOOST_PATH}
# For Linux
else
    if ! [ -d "${ROOT_DIR}/clang+llvm"  ]; then
        ${ROOT_DIR}/LLM4Veri/scripts/requires/get_llvm.sh
    fi
fi


export PATH=${ROOT_DIR}/clang+llvm/bin:$PATH
export LD_LIBRARY_PATH=${ROOT_DIR}/clang+llvm/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}
export CC=clang
export CXX=clang++


# install llvm pass
cd ${ROOT_DIR}/LLM4Veri/llvm/llvm-pass/src
cp ${ROOT_DIR}/LLM4Veri/llvm/llvm-pass-old/src/*.h ./
cd ${ROOT_DIR}/LLM4Veri/llvm/llvm-pass
rm -rf build
mkdir build
cd ${ROOT_DIR}/LLM4Veri/llvm/llvm-pass/build
rm -rf ./*
cmake ..
make
cp -f ${ROOT_DIR}/LLM4Veri/llvm/llvm-pass/build/src/libCallGraph.so ${ROOT_DIR}/LLM4Veri/llvm/lib/veri-llvm-pass.so

# install clang wrapper
cd ${ROOT_DIR}/LLM4Veri/llvm/veri-clang
make clean
make
PREFIX=${ROOT_DIR}/LLM4Veri/llvm make install
make all_done

echo "Installation completed. Everything's fine!"
