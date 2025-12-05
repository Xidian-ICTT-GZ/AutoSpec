#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import os, sys, re
import argparse
import getopt
import datetime
import shutil
import logging
from typing import List
current_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(current_path))
from src.framac import *

# 定义函数，合并ACSL规约
def merge_acsl(files):
    # 正则表达式匹配ACSL规约注释
    pattern = r"/\*(.|[\r\n])*?\*/"

    # 存储ACSL规约的字典
    acsl_dict = {}

    # 遍历文件列表
    for file in files:
        # 打开文件并读取内容
        with open(file, 'r') as f:
            content = f.read()

        # 查找ACSL规约注释
        acsl_comments = re.findall(pattern, content)

        # 遍历ACSL规约注释，并存储到字典中
        for comment in acsl_comments:
            print(comment)
            # 去除注释中的换行符和空格
            comment = comment.replace('\n', '').replace('\r', '')
            comment = re.sub(r' +', ' ', comment)

            # 存储ACSL规约到字典中
            if comment not in acsl_dict:
                acsl_dict[comment] = file

    # 拼接ACSL规约，生成结果字符串
    result = ''
    for comment, file in acsl_dict.items():
        # 读取文件名
        file_basename = os.path.basename(file)

        # 拼接注释
        result += f'\n\n/* {file_basename} */\n{comment}'

    return result


def postprocess_for_file_pair(file_pair_list, folder_name):
    # create output folder
    if folder_name[-1] == "/":
        output_folder = folder_name[:-1] + "_postprocess"
    else:
        output_folder = folder_name + "_postprocess"
    
    # create output folder if it does not exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    else:
        # if folder is not empty, delete it
        if len(os.listdir(output_folder)) == 0:
            pass
        else:
            try:
                shutil.rmtree(output_folder)
                os.makedirs(output_folder)
            except OSError as e:
                print("Error: %s : %s" % (output_folder, e.strerror))
    
    # ===== func 'simplify_acsl' start =====
    def simplify_acsl(pair_0, pair_1, infolder, outfolder):
        # create a list to store the information of all the failed goals
        fdict_list = []
        # open the file and read the content into a list
        with open(os.path.join(infolder, pair_1), 'r') as f:
            content = f.readlines()
            # iterate over each line in the content list
            for line_index in range(len(content)):
                # if the line contains the goal name, we check if it is a failed goal
                if "file " + pair_0 in content[line_index] or "Goal Assigns " in content[line_index]:
                    # two flags to indicate if the goal is proved true or proved false
                    prove_true_flag = False
                    prove_false_flag = False
                    # the line index of the current line
                    tmp_index =  line_index
                    # iterate over each line until we reach the end of the file
                    while tmp_index + 1 < len(content):
                        # get the content of the next line
                        next_line_content = content[tmp_index+1]
                        # if the next line contains "Prove: true", the goal is proved true
                        if "Prove: true." in next_line_content or ("Prover " in next_line_content and "returns Valid (" in next_line_content):
                            prove_true_flag = True
                            break
                        # if the next line contains "Prove: false", the goal is proved false
                        elif "Prove: false." in next_line_content or ("Prover " in next_line_content and "returns Timeout (" in next_line_content):
                            #print(next_line_content)
                            prove_false_flag = True
                        # if the next line contains "----------", we reach the end of the file
                        elif "----------" in next_line_content:
                            break
                        # if the next line does not contain anything useful, we continue
                        else:
                            pass
                        # move to the next line
                        tmp_index = tmp_index + 1

                    # if the goal is proved true, we continue to the next goal
                    if prove_true_flag:
                        continue

                    # if the goal is proved false, we extract the goal name and line number
                    if prove_false_flag:
                        if "Goal Assigns " in content[line_index]:
                            merged_content = content[line_index].strip() + " " + content[line_index + 1].strip()
                            # print(merged_content)
                            [(goal, fnstr, linestr)] = re.findall(r"Goal (.*) in '(.*)' .*: Effect at line (.*)", merged_content)
                        else:
                            [(goal, linestr, fnstr)] = re.findall(r'Goal (.*)\(file .*.c, (.*)\)(.*):', content[line_index])
                        goal = goal.strip()
                        if ")" in linestr:
                            linestr = linestr.split(")")[0]
                        lineint = int(linestr.replace("line ", ""))
                        if fnstr != '' and "in '" in fnstr:
                            fnstr = fnstr.replace("in '", "").replace("'","")
                        # print({"goal": goal, "line": lineint, "fn": fnstr})
                        fdict_list.append({"goal": goal, "line": lineint, "fn": fnstr})
                        
        # if fdict_list's goal are all assign
        all_assign_flag = True
        for each_dict in fdict_list:
            if not "Assigns " in each_dict['goal']:
                all_assign_flag = False
        if fdict_list != [] and  all_assign_flag == True:
            return -1

        # Open the file
        with open(os.path.join(infolder, each_pair[0]), 'r') as f:
            # Read the file line by line
            content = f.readlines()
            # For each dictionary in the list of dictionaries
            for each_dict in fdict_list:
                # Replace the line in the file that is specified in the dictionary with a newline
                if "Assigns " in each_dict['goal']:
                    continue
                content[each_dict['line'] - 1] = "//\n"
            
            # remove empty lines
            content = [x for x in content if x != "//\n"]
            
        # write content into new file
        with open(os.path.join(outfolder, each_pair[0]), 'w') as f:
            f.writelines(content)

        return 1
    
    # ===== func 'simplify_acsl' end =====

    for each_pair in file_pair_list:
        # check if the second item in each pair contains the string "_Invalid."
        if "_Invalid." in each_pair[1]:
            # if it does, skip to the next iteration of the loop
            continue
        # check if the second item in each pair contains the string "_Pass_"
        elif "_Pass_" in each_pair[1]:
            # if it does, copy the each_pair[0] file to output_folder
            shutil.copy(os.path.join(folder_name, each_pair[0]), output_folder)
            # also copy the each_pair[1] file to output_folder
            shutil.copy(os.path.join(folder_name, each_pair[1]), output_folder)
            # skip to the next iteration of the loop
            continue
        # if the second item in each pair does not contain either of the strings above
        else:
            # execute the following process
            pass

        # loop until the goal is proved true
        attempt = 0
        framac_result_type = each_pair[1]
        genfile, acsl_cmd_r = each_pair[0], each_pair[1]
        infolder = folder_name
        outfolder = output_folder
        framac_result_file = ""
        last_framac_result_file = ""
        while "Fail_" in framac_result_type:
            # simplify ACSL
            ret = simplify_acsl(genfile, acsl_cmd_r, infolder, outfolder)

            if ret == -1:
                break

            # remove frama_result_file
            if framac_result_file != "":
                os.remove(framac_result_file)
            
            # run frama-c
            framac_result_type, framac_result_file, _ = run_framac_with_wp(output_folder, each_pair[0])
            print("out:", framac_result_file)
            # The name of the folder to be generated
            infolder, outfolder = output_folder, output_folder
            # The name of the file to be generated
            genfile, acsl_cmd_r = os.path.join(outfolder, each_pair[0]), framac_result_file.rsplit("/", 1)[-1]
            
            if attempt > 1:
                if last_framac_result_file == framac_result_file:
                    break
            elif attempt > 10: # If the user has entered the wrong password more than 10 times, break out of the loop
                raise Exception("Frama-C cannot prove the goal after 10 attempts.")
                break # Break out of the loop
            attempt = attempt + 1 # Add one to the number of attempts
            last_framac_result_file = framac_result_file
        
        print("\nlast iter result: ", each_pair[1], ", current iter result: ", framac_result_type)
        print("||||||||||||||||||\n")


def main(argv: List[str]) -> None:
    # set logging.INFO rather than logging.DEBUG
    logging.basicConfig(level=logging.INFO)
    # Parse the command line arguments
    folder_name = parse_args(argv)
    if "," in folder_name:
        folder_name_list = folder_name.split(",")
    else:
        folder_name_list = [folder_name]

    all_file_list = []
    for each_file_name in folder_name_list:
        # iter every file in a folder, and get it absolute path
        for root, dirs, files in os.walk(each_file_name):
            for file in files:
                # get file absolute path
                # file_path = os.path.join(root, file)
                all_file_list.append(file)
    
    # pair
    file_pair_list = []
    for each_c_file in all_file_list:
        if "_gen_" in each_c_file and (each_c_file.endswith(".c") or each_c_file.endswith(".cpp")):
            try:
                rname = each_c_file.rsplit(".", 1)[0].replace("_gen_", "_fstd_")
                for each_framac_result in all_file_list:
                    if "_gen_" in each_framac_result:
                        continue
                    elif rname in each_framac_result:
                        file_pair_list.append((each_c_file, each_framac_result))
                    else:
                        continue
            except:
                continue

    postprocess_for_file_pair(file_pair_list, folder_name)

    # 处理文件列表，去除重复文件
    qualified_file = []
    for file in all_file_list:
        if "_gen_" in file:
            pass

    # 测试代码，合并示例文件
    #result = merge_acsl(acsl_file_list)
    #print(result)

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
            print('main.py -f <folder>')
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