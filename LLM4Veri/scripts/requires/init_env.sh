#!/usr/bin/env bash

DIR_BACKUP=$(pwd)
cd $(dirname $BASH_SOURCE)
ROOT_DIR="$(dirname $(dirname $(dirname `pwd`)))"
cd $DIR_BACKUP

read -n 1 -p "Is this your tool's root directory: $ROOT_DIR? (Y/n): " c
echo ""

if [[ $c = n ]] || [[ $c = N ]]; then
    read -p "Define your tool's root directory here: " ROOT_DIR
fi

echo "Root directory is set to be: $ROOT_DIR"
export ROOT_DIR

# All
export PATH=${ROOT_DIR}/clang+llvm/bin:${ROOT_DIR}/LLM4Veri/llvm/bin:$PATH
export LD_LIBRARY_PATH=${ROOT_DIR}/clang+llvm/lib:${LD_LIBRARY_PATH}
export LLVM_COMPILER=clang
export ASAN_OPTIONS=detect_leaks=0
export VERI_LIB_PATH=${ROOT_DIR}/LLM4Veri/llvm/

LLVM_VERSION=""
if command -v llvm-config >/dev/null 2>&1; then 
    LLVM_VERSION=$(llvm-config --version) 
else 
    LLVM_VERSION="Unknown"
fi

if [[ "$LLVM_VERSION" == "Unknown" ]];then
    echo "Can not find clang+llvm, please check llvm-config"
    echo "Fail to perform initiation"
else
    echo -e "The full version of clang+llvm is "$LLVM_VERSION"; \c"
    LLVM_MAIN_VERSION=${LLVM_VERSION%%.*}
    echo "The main version of clang+llvm is "$LLVM_MAIN_VERSION
fi
cd $DIR_BACKUP
