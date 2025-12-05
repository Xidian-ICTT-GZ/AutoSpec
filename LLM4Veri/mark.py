#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import os, sys, re
import argparse
import getopt
import datetime
import logging
import subprocess
import pickle
from src.baselib import *
from typing import List


SPEC_FILE = "SpecLoC.txt"

def RunClangCommand(file_name):
    # Command line
    os.system("rm -f tmp.o && rm -f " + SPEC_FILE)
    VERI_CLANG_Command = ["veri-clang", "-O0", "-c", file_name, "-o", "tmp.o"]

    # create subprocess according to the value of check_STDOUT and check_STDERR
    process = subprocess.Popen(VERI_CLANG_Command, close_fds=True, preexec_fn=os.setpgrp)
    logging.info("[CMD] Running `" + ' '.join(VERI_CLANG_Command) + "`")
    process.communicate()


def GetSpecLoc():
    if os.path.exists(SPEC_FILE):
        with open(SPEC_FILE, 'r') as f:
            lines = f.readlines()
            SpecLocList = []
            for line in lines:
                line = line.strip('\n')
                SpecLocList.append(line)
            return SpecLocList
    else:
        print("Error: SpecLoC.txt does not exist")
        sys.exit(2)


def TransformDict(SpecLocList):
    SpecDictList = []
    for SpecLoc in SpecLocList:
        SpecDict = {}
        func_name, func_loc, loop_loc = SpecLoc.split('===')
        SpecDict['func_name'] = func_name
        
        if ":" in func_loc:
            file_name, func_loc = func_loc.rsplit(':')
            SpecDict['file_name'] = file_name
            SpecDict['func_loc'] = int(func_loc)
        else:
            print("func_loc error")
            sys.exit(2)

        if loop_loc == '0':
            SpecDict['loop_loc'] = []
        elif ',' in loop_loc:
            loop_loc = loop_loc.split(',')
            #SpecDict['loop_loc'] = list(map(int, loop_loc)) # Convert all strings in a list to integers
            SpecDict['loop_loc'] = list(loop_loc)
        elif loop_loc.replace('@', '').isdigit():
            #SpecDict['loop_loc'] = [int(loop_loc)]
            SpecDict['loop_loc'] = [loop_loc]
        else:
            print(loop_loc)
            print("loop_loc does not exist")
        SpecDictList.append(SpecDict)
    return SpecDictList


def MartkedSourceCode(file_name, SpecDictList):
    # spit file_name from last '/' and get the prefix and suffix
    prefix_str, mfName, suffix_str = split_file_name(file_name)

    # task ID, start from 1
    taskID = 1
    MSLines = []
    InfillLines = []
    SAVE_PICKLE = dict()
    SAVE_PICKLE['CurTaskID'] = 1
    SAVE_PICKLE['Round'] = 1
    SAVE_PICKLE['Iteration'] = 1
    SAVE_PICKLE['Status'] = 0
    SAVE_PICKLE['llms_query_times'] = datetime.timedelta(0)
    SAVE_PICKLE['total_solve_time'] = datetime.timedelta(0)
    SAVE_PICKLE['simplified_time'] = datetime.timedelta(0)
    SAVE_PICKLE['tokens_usage'] = 0
    SAVE_PICKLE['spec_num_original'] = 0
    SAVE_PICKLE['spec_num_simplified'] = 0
    SAVE_PICKLE['TaskList'] = [] # 0 -> not marked, 1 -> contract, 2 -> loop invariant, 3 -> outter loop invariant
    
    # Read the source code
    if "code2inv" in file_name or "SVCOMP" in file_name or "multi-phase-loops" in file_name or "fib_46_" in file_name:
        target_file_name = file_name.replace(".c", "_m.c")
    else:
        target_file_name = file_name
    
    with open(target_file_name, 'r') as f:
        # call readlines() to get a list of lines
        MSLines = f.readlines()
        InfillLines = MSLines.copy()
        for i in range(0, len(MSLines)):
            lineNO = i + 1
            # print(lineNO, MSLines[i], end='')
            for eachfun in SpecDictList:
                if eachfun['func_loc'] == lineNO:
                    if eachfun['loop_loc'] != []:
                        for eachloop in eachfun['loop_loc']:
                            if eachloop.startswith('@'):
                                SAVE_PICKLE['TaskList'].append(3)
                                loopLocNO = int(eachloop.replace('@', ''))
                            else:
                                SAVE_PICKLE['TaskList'].append(2)
                                loopLocNO = int(eachloop)
                            # get Space character prefix
                            space_prefix = re.match(r'\s*', MSLines[loopLocNO-1]).group()
                            # mark the loop invariant
                            SAVE_PICKLE[str(taskID)] = []
                            MSLines[loopLocNO-1] = space_prefix + "/* " + str(taskID) + ". LOOP INVARIANT */\n" + MSLines[loopLocNO-1]
                            if taskID == 1:
                                InfillLines[loopLocNO-1] = space_prefix + "/* @ >>> INFILL <<< */\n" + InfillLines[loopLocNO-1]
                            else:
                                InfillLines[loopLocNO-1] = space_prefix + "\n" + InfillLines[loopLocNO-1]
                            taskID = taskID + 1
                    # get Space character prefix
                    space_prefix = re.match(r'\s*', MSLines[lineNO-1]).group()
                    # mark the function contract
                    SAVE_PICKLE[str(taskID)] = []
                    SAVE_PICKLE['TaskList'].append(1)
                    MSLines[lineNO-1] = "/* " + str(taskID) + ". FUNC CONTRACT */\n" + MSLines[lineNO-1]
                    if taskID == 1:
                        InfillLines[lineNO-1] = space_prefix + "/* @ >>> INFILL <<< */\n" + InfillLines[lineNO-1]
                    else:
                        InfillLines[lineNO-1] = space_prefix + "\n" + InfillLines[lineNO-1]
                    taskID = taskID + 1
    # remove target_file_name
    if "code2inv" in file_name or "SVCOMP" in file_name or "multi-phase-loops" in file_name or "fib_46_" in file_name:
        os.system("rm -f " + target_file_name)
    pass
    SAVE_PICKLE['MSLines'] = MSLines

    # Save as list
    with open(file_name + ".pickle", "wb") as output:
        pickle.dump(SAVE_PICKLE, output)
    
    # Load the list
    with open(file_name + ".pickle", "rb") as data:
        LOADED_PICKLE = pickle.load(data)
        #print(LOADED_PICKLE)

    InfillLines = get_infill_lines(SAVE_PICKLE)

    # Write into Another New file with the "_marked" suffix
    write_into_marked_c_file(prefix_str, mfName, suffix_str, MSLines)
    
    # Write into Another New file with the "_infilled" suffix
    write_into_infilled_c_file(prefix_str, mfName, suffix_str, InfillLines, True)


def preprocess(file_name):
    if "code2inv" in file_name or "SVCOMP" in file_name or "multi-phase-loops" in file_name or "fib_46_" in file_name:
        new_file_name = file_name.replace(".c", "_m.c")
        with open(file_name, 'r') as f:
            # call readlines() to get a list of lines
            lines = f.readlines()
            for i in range(0, len(lines)):
                if "static_assert(" in lines[i]:
                    lines[i] = lines[i].replace("static_assert(", "//@ assert ").replace(");", ";")
                elif "europa_assert(" in lines[i]:
                    lines[i] = lines[i].replace("europa_assert(", "//@ assert ").replace(");", ";")
                elif "__VERIFIER_assert(" in lines[i]:
                    lines[i] = lines[i].replace("__VERIFIER_assert(", "//@ assert ").replace(");", ";")
                elif "__VERIFIER_assert (" in lines[i]:
                    lines[i] = lines[i].replace("__VERIFIER_assert (", "//@ assert ").replace(");", ";")
                elif "assert(" in lines[i]:
                    lines[i] = lines[i].replace("assert(", "//@ assert ").replace(");", ";")
                elif "assert (" in lines[i]:
                    lines[i] = lines[i].replace("assert (", "//@ assert ").replace(");", ";")
                elif "&& __VERIFIER_nondet_int()" in lines[i]:
                    lines[i] = lines[i].replace("&& __VERIFIER_nondet_int()", "")
                elif "= __VERIFIER_nondet_int()" in lines[i]:
                    lines[i] = ""
                
                if "// invariant " in lines[i] or "// invarian " in lines[i]:
                    lines[i] = ""
                elif "assume(" in lines[i]:
                    lines[i] = ""
                elif "assume (" in lines[i]:
                    lines[i] = ""
                elif "europa_assume(" in lines[i]:
                    lines[i] = ""
                elif "europa_assume (" in lines[i]:
                    lines[i] = ""
                elif "__VERIFIER_assume(" in lines[i]:
                    lines[i] = ""
                elif "__VERIFIER_assume (" in lines[i]:
                    lines[i] = ""
                elif "europa_make_symbolic(" in lines[i]:
                    lines[i] = ""
                elif "europa_make_symbolic (" in lines[i]:
                    lines[i] = ""
                elif "europa_invariant(" in lines[i]:
                    lines[i] = ""
                elif "europa_invariant (" in lines[i]:
                    lines[i] = ""

            with open(new_file_name, 'w') as f:
                f.writelines(lines)
    else:
        return file_name
        
    
    return new_file_name

def main(argv: List[str]) -> None:
    # set logging.INFO rather than logging.DEBUG
    logging.basicConfig(level=logging.INFO)

    # Parse the command line arguments
    file_name = parse_args(argv)

    # Pre-processing for code2inv
    file_name_m = preprocess(file_name)

    # Run veri-clang to mark the source code
    RunClangCommand(file_name_m)

    # get SpecLoC
    SpecLocList = GetSpecLoc()

    # Transform SpecLoC to SpecDict
    SpecDictList = TransformDict(SpecLocList)
    for each in SpecDictList:
        print(each)

    # output the marked source code
    MartkedSourceCode(file_name, SpecDictList)

    # End


def parse_args(argv: List[str]) -> argparse.Namespace:
    # Parse the command line arguments using the getopt module
    try:
        opts, args = getopt.getopt(argv, "hf:", ["help", "File="])

    except getopt.GetoptError:
        print('Error: main.py -f <File>')
        sys.exit(2)

    file_name = ""

    # Process the options list into elements of a list
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print('mark.py -f <file>')
            sys.exit()
        elif opt in ("-f", "--file"):
            file_name = arg

    if file_name == "":
        print('Error: file is not specified, or the string is not specified')
        print('Tips: Using -h to view help')
        sys.exit(2)

    # Print the arguments list, which contains all arguments that don't start with '-' or '--'
    for i in range(0, len(args)):
        print('Argument %s is: %s' % (i + 1, args[i]))

    return file_name


if __name__ == "__main__":
    starttime = datetime.datetime.now()
    main(sys.argv[1:])
    endtime = datetime.datetime.now()
    print("\nstart time: ", starttime)
    print("end time: ", endtime)
    print("@@@ Finished @@@")