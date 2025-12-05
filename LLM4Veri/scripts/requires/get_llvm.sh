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

CPU=`arch`
if [ "${CPU}" == "i686" ] || [ "${CPU}" == "i386" ] ; then
    CPU=x86_32
elif [ ${CPU} == "aarch64" ]; then
    CPU=aarch64
elif [ ${CPU} == "x86_64" ]; then
    CPU=x86_64
else
    die "Unknown cpu type."
fi

set -eux

PREFIX=${ROOT_DIR}

cd ${ROOT_DIR}

if [ $(command uname) == "Darwin" ]; then
	# For Mac
	LLVM_VER=${LLVM_VER:-12.0.0}
	LINUX_VER=${LINUX_VER:-darwin}
	TAR_NAME=clang+llvm-${LLVM_VER}-x86_64-apple-${LINUX_VER}
else
	# For Linux
	if [ ${CPU} == "x86_64" ]; then
		LINUX_VER=${LINUX_VER:--ubuntu-16.04}
	elif [ ${CPU} == "aarch64" ]; then
		LINUX_VER=""
	fi
	LLVM_VER=${LLVM_VER:-12.0.1}
	TAR_NAME=clang+llvm-${LLVM_VER}-${CPU}-linux-gnu${LINUX_VER}
fi

LLVM_DEP_URL=https://github.com/llvm/llvm-project/releases/download/llvmorg-${LLVM_VER}/${TAR_NAME}.tar.xz

wget -c $LLVM_DEP_URL --no-check-certificate
tar -C ${PREFIX} -xf ${TAR_NAME}.tar.xz
rm ${TAR_NAME}.tar.xz
rm -rf ${PREFIX}/clang+llvm
mv ${PREFIX}/clang+llvm-${LLVM_VER}* ${PREFIX}/clang+llvm

set +x
