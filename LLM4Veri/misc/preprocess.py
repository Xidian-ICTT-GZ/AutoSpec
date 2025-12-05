#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import os, sys
import argparse
import getopt
import datetime
import logging
import hashlib
import shutil
from typing import List
current_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(current_path))
from src.framac import *


def loop_analysis():
    # frama-c -eva -loop -main test -loop-log a:log IP_string_m.c > log.txt  # -eva -cg cg
    pass


def get_call_graph_from_dot(dotfile):
    # read cg.dot
    with open(dotfile, "r") as cgfile:
        cg = cgfile.readlines()
        
    # get call graph
    


def run_framac_with_eva(filelist, unique_hash, functionEntry):
    FRAMAC_Command = ["frama-c", "-eva", "-cg", unique_hash + "/cg.dot"]
    if functionEntry != "":
        FRAMAC_Command.extend(["-main", functionEntry])
    FRAMAC_Command.extend(filelist)
    print(FRAMAC_Command)
    
    # create subprocess according to the value of check_STDOUT and check_STDERR
    process = create_FRAMAC_subprocess(FRAMAC_Command, Check_STDOUT, Check_STDERR)
    logging.info("[CMD] Running `" + ' '.join(FRAMAC_Command) + "`")

    output_std_file_name = unique_hash + "/stdout.txt"
    output_err_file_name = unique_hash + "/stderr.txt"

    try:
        # join subprocess
        if Check_STDOUT == 1 or Check_STDERR == 1:
            stdoutdata, stderrdata = process.communicate(timeout=SubprocessTimeout)
            if stdoutdata != b'':
                with open (output_std_file_name, "wb") as stdfile:
                    #stdfile.write(bytes(str(pattern)+"\n", encoding = "utf8"))
                    stdfile.write(stdoutdata)
            if stderrdata != b'':
                with open (output_err_file_name, "wb") as stdfile:
                    stdfile.write(stderrdata)
        else:
            process.communicate(timeout=SubprocessTimeout)
    
    except subprocess.TimeoutExpired:
        # process.kill()
        # process.terminate()
        subprocess.check_call(["sudo", "kill", str(process.pid)])
        #os.waitpid(process.pid, 0)
        logging.error("Timeout for subprocess when running frama-c on" + ' '.join(os.path.join(Output_folder, filelist)))
    
    except Exception as e:
        print("\033[34m\tUnknown Exception" + "\033[0m")
        print(e)
        raise e


def preprocess(filelist, functionEntry):
    # get a hash value from filelist
    hash = hashlib.md5() # create a sha256 hash object
    for file_path in filelist:
        hash.update(file_path.encode()) # encode each string and update the hash object
    unique_hash = hash.hexdigest()[:8] # get the hash value

    # First, check if the directory exists and if so, remove it
    if os.path.exists(unique_hash):
        shutil.rmtree(unique_hash)
    # Create the directory
    os.mkdir(unique_hash)

    # run frama-c with eav, call graph
    run_framac_with_eva(filelist, unique_hash, functionEntry)

    # analyze cg.dot and get call graph
    call_graph = get_call_graph_from_dot(unique_hash + "/cg.dot")
    
    # mark loop


def main(argv: List[str]) -> None:
    # set logging.INFO rather than logging.DEBUG
    logging.basicConfig(level=logging.INFO)
    # Parse the command line arguments
    filestr, functionEntry = parse_args(argv)
    
    if " " in filestr.strip():
        filelist = filestr.split(" ")
    else:
        filelist = [filestr]
    # sort the filelist
    filelist = sorted(filelist)
    
    preprocess(filelist, functionEntry)
    # End


def parse_args(argv: List[str]) -> argparse.Namespace:
    # Parse the command line arguments using the getopt module
    try:
        opts, args = getopt.getopt(argv, "hf:m:", ["help", "FileList=", "MainFunction="])

    except getopt.GetoptError:
        print('Error: main.py -f <Folder>')
        sys.exit(2)

    filestr = ""
    functionEntry = ""

    # Process the options list into elements of a list
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print('main.py -f <File> -m <entry function>')
            sys.exit()
        elif opt in ("-f", "--filelist"):
            filestr = arg
        elif opt in ("-m", "--main"):
            functionEntry = arg

    if filestr == "":
        print('Error: folder is not specified, or the string is not specified')
        print('Tips: Using -h to view help')
        sys.exit(2)

    # Print the arguments list, which contains all arguments that don't start with '-' or '--'
    for i in range(0, len(args)):
        print('Argument %s is: %s' % (i + 1, args[i]))

    return filestr, functionEntry


if __name__ == "__main__":
    starttime = datetime.datetime.now()
    main(sys.argv[1:])
    endtime = datetime.datetime.now()
    print("\nstart time: ", starttime)
    print("end time: ", endtime)
    print("@@@ Finished @@@")