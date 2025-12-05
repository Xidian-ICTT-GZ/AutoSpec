#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import os, sys
import argparse
import getopt
import datetime
from typing import List

def main(argv: List[str]) -> None:
    # Parse the command line arguments
    folder_name = parse_args(argv)

    all_num = 0
    uk_num = 0
    gen_num = 0
    invaild_num = 0
    fail_num = 0
    pass_num = 0
    err_num = 0

    # Start
    try:
        # get all files in the folder
        files_list = os.listdir(folder_name)
        all_num = len(files_list)

        for each_file in files_list:
            if "_Fail" in each_file:
                fail_num += 1
            elif "_Pass" in each_file:
                pass_num += 1
            elif "_Invalid" in each_file:
                invaild_num += 1
            elif "_gen" in each_file:
                gen_num += 1
            elif "_UK" in each_file:
                uk_num += 1
            else:
                if "_ferr_" in each_file:
                    err_num += 1
                    continue
                else:
                    raise Exception("Error: file name is not correct: " + each_file)
            
    except Exception as e:
        print(e)
        raise e
    
    print("all_num: ", all_num - err_num, ", sum: ", invaild_num + fail_num + pass_num + gen_num + uk_num - err_num)
    print("gen_num: ", gen_num)
    print("invaild_num: ", invaild_num)
    print("Vaild_num: ", fail_num + pass_num)
    print("fail_num: ", fail_num)
    print("pass_num: ", pass_num)
    print("uk_num: ", uk_num)
    print("err_num: ", err_num)

    # End


def parse_args(argv: List[str]) -> argparse.Namespace:
    # Parse the command line arguments using the getopt module
    try:
        opts, args = getopt.getopt(argv, "hf:", ["help", "Folder="])

    except getopt.GetoptError:
        print('Error: main.py -f <Folder>')
        sys.exit(2)

    folder_name = ""

    # Process the options list into elements of a list
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print('main.py -f <Folder>')
            sys.exit()
        elif opt in ("-f", "--folder"):
            folder_name = arg

    if folder_name == "":
        print('Error: folder is not specified, or the string is not specified')
        print('Tips: Using -h to view help')
        sys.exit(2)

    # Print the arguments list, which contains all arguments that don't start with '-' or '--'
    for i in range(0, len(args)):
        print('Argument %s is: %s' % (i + 1, args[i]))

    return folder_name


if __name__ == "__main__":
    starttime = datetime.datetime.now()
    main(sys.argv[1:])
    endtime = datetime.datetime.now()
    print("\nstart time: ", starttime)
    print("end time: ", endtime)
    print("@@@ Finished @@@")