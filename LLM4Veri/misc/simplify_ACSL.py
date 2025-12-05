#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import os, sys, re
import argparse
import getopt
import datetime
import shutil
import logging
import copy
import pickle
from typing import List
current_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(current_path))
from src.baselib import *
from src.framac import *


def simplify_spec_result(gpt_file, outputfolder):
    total_simplified_time = datetime.timedelta(0)

    # whether file exits
    pickleFile = gpt_file+'.pickle'
    SAVE_PICKLE = {}
    if os.path.exists(pickleFile):
        # Load the pickle
        with open(pickleFile, "rb") as data:
            SAVE_PICKLE = pickle.load(data)
            if SAVE_PICKLE['Status'] == 0:
                print("Please simplify after verification is passed")
            else:
                pass
    else:
        print("Not found "+ gpt_file+'.pickle' + "file.")
        sys.exit(-1)
    
    # whether outputfolder exits
    if os.path.exists(outputfolder):
        # delete outputfolder
        shutil.rmtree(outputfolder)
    os.makedirs(outputfolder)
   
    # Start

    # wite original file into outputfolder
    _, mfName, suffix_str = split_file_name(gpt_file)
    InfillLines = get_infill_lines(SAVE_PICKLE)
    outputfinalfile = write_into_final_c_file(outputfolder, mfName, suffix_str, InfillLines)
    # simplify
    SAVE_PICKLE_tmp = copy.deepcopy(SAVE_PICKLE)

    task_num = len(SAVE_PICKLE['TaskList'])
    spec_num_original = 0
    spec_num_redundant = 0
    for i in range(task_num, 0, -1):
        if SAVE_PICKLE[str(i)] == []:
            continue
        else:
            for each in SAVE_PICKLE[str(i)]:
                if "loop assigns " in each:
                    continue
                SAVE_PICKLE_tmp[str(i)].remove(each)
                
                # run framac to see whether it is useful
                InfillLines = get_infill_lines(SAVE_PICKLE_tmp)
                outputfinalfile = write_into_final_c_file(outputfolder, mfName, suffix_str, InfillLines, True)
                print(outputfinalfile)
                
                _, gfileName, gfileSuffix = split_file_name(outputfinalfile)
                print("Performing specifications simplifies")
                output_result_type, _, _, simplified_time = run_framac_with_wp(outputfolder, gfileName + gfileSuffix)
                total_simplified_time += simplified_time
                if "Pass_" in output_result_type:
                    print("Succuessfully simplified:", each)
                    SAVE_PICKLE = copy.deepcopy(SAVE_PICKLE_tmp)
                    if not "loop assigns " in each:
                        spec_num_original += 1
                        spec_num_redundant += 1
                else:
                    if not "loop assigns " in each:
                        spec_num_original += 1
                print(output_result_type, simplified_time)

                # delete the SAVE_PICKLE_tmp and reset
                del SAVE_PICKLE_tmp
                SAVE_PICKLE_tmp = copy.deepcopy(SAVE_PICKLE)

    del SAVE_PICKLE_tmp

    # output
    InfillLines = get_infill_lines(SAVE_PICKLE)
    outputfinalfile = write_into_final_c_file(outputfolder, mfName, suffix_str, InfillLines, True)
    SAVE_PICKLE['simplified_time'] += total_simplified_time
    SAVE_PICKLE['spec_num_original'] = spec_num_original
    SAVE_PICKLE['spec_num_simplified'] = spec_num_original - spec_num_redundant
    print("total_simplified_time =", total_simplified_time)
    final_spec_num_change_str = str(spec_num_original) + " -> " +str(spec_num_original - spec_num_redundant)
    print("spec num =", final_spec_num_change_str)

    with open(pickleFile, "wb") as data:
        pickle.dump(SAVE_PICKLE, data)

    with open(os.path.join(outputfolder, "final_result"), "w") as f:
                    f.write("Pass\n")
                    f.write(str(SAVE_PICKLE))
                    f.write('\n' + Pikachu_str)
    
    return total_simplified_time, final_spec_num_change_str  
    # End


def main(argv: List[str]) -> None:
    # Parse the command line arguments
    gpt_file, outputfolder = parse_args(argv)
    simplify_spec_result(gpt_file, outputfolder)


def parse_args(argv: List[str]) -> argparse.Namespace:
    # Parse the command line arguments using the getopt module
    try:
        opts, args = getopt.getopt(argv, "hvf:o:", ["help", "version", "File=", "Output="])

    except getopt.GetoptError:
        print('Error: main.py -f <File> -t <task> -o <outputfolder>')
        sys.exit(2)

    gpt_file = ""
    output_folder = ""

    # Process the options list into elements of a list
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print('Syntax:')
            print('\tmain.py -f <File> -o <outputfolder>', "\n")
            sys.exit()
        elif opt in ("-v", "--version"):
            print('version 1.0.0')
            sys.exit()
        elif opt in ("-f", "--file"):
            gpt_file = arg
        elif opt in ("-o", "--output"):
            output_folder = arg

    if gpt_file == "":
        print('Error: file is not specified')
        print('Tips: Using -h to view help')
        sys.exit(2)
    
    if output_folder == "":
        print("[DEBUG] output folder is not specified, use default 'out' folder")
        output_folder = auto_naming_output_folder("", gpt_file, True)

    print('[DEBUG] gpt_file = ', gpt_file)
    print('[DEBUG] output_folder = ', output_folder)


    # Print the arguments list, which contains all arguments that don't start with '-' or '--'
    for i in range(0, len(args)):
        print('Argument %s is: %s' % (i + 1, args[i]))
    
    return gpt_file, output_folder


if __name__ == "__main__":
    starttime = datetime.datetime.now()
    main(sys.argv[1:])
    endtime = datetime.datetime.now()