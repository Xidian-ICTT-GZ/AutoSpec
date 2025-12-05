#!/usr/bin/env python3

import os
import sys
import re
import getopt
from typing import List


def parse_args(argv: List[str]):
    process_folder_list = []
    try:

        opts, _ = getopt.getopt(argv[1:], "f:", ["folder"])

        for opt, arg in opts:
            if opt in ("-f", "--folders"):
                process_folder_list = arg.split(" ")

        if len(process_folder_list) == 0:
            print("No result folder is specified.")
            print(f"Usage: python3 ./stat.py -f \"folder1 folder2 ...\"")

    except getopt.GetoptError:
        sys.exit(1)

    return process_folder_list


def obtain_filename_iteration(file):
    filename, iteration = "", 0

    filename = re.findall(r"(.*)_000.*", file)
    if len(filename) > 0:
        filename = filename[0]
    iteration = re.findall(r".*_000(.)", file)
    if len(iteration) > 0:
        iteration = iteration[0]

    return filename, iteration


def mk_stat_res_for_single_folder(folder):
    stat_dict = {}
    stat_res = {}

    if os.path.exists(folder):
        file_list = os.listdir(folder)

        # obtain the last iteartion for each file
        for file in file_list:
            filename, iteration = obtain_filename_iteration(file)
            if filename == "" or iteration == 0:
                continue

            if filename in stat_dict:
                if stat_dict[filename] < iteration:
                    stat_dict[filename] = iteration
            else:
                stat_dict[filename] = iteration

        if len(stat_dict) > 0:
            for file in stat_dict:
                res_file = os.path.join(folder, f"{file}_000{stat_dict[file]}",
                                        "final_result")
                if os.path.exists(res_file):
                    with open(res_file, "r") as f:
                        res = f.readline()

                        if len(res) > 0:
                            stat_res[file] = {
                                "iter": stat_dict[file],
                                "res": res
                            }
                        else:
                            stat_res[file] = {"iter": "-", "res": "Empty"}
                else:
                    stat_res[file] = {"iter": "-", "res": "Empty"}

    return stat_res


def print_res(final_res_dict):
    if len(final_res_dict) > 0:
        for file in final_res_dict:
            res = final_res_dict[file]
            print(f"{file}\t{res['suc']}\t{res['iter']}")


def main(argv: List[str]):
    folder_list = parse_args(argv)

    final_res_dict = {}

    for folder in folder_list:
        stat_res = mk_stat_res_for_single_folder(folder)
        for file in stat_res:
            if file in final_res_dict:
                suc_count = final_res_dict[file]["suc"]
                if "Pass" in stat_res[file]["res"]:
                    suc_count = suc_count + 1
                iter_str = final_res_dict[file]["iter"] + "," + stat_res[file][
                    "iter"]
                final_res_dict[file] = {"suc": suc_count, "iter": iter_str}

            else:
                is_suc = True if "Pass" in stat_res[file]["res"] else False
                final_res_dict[file] = {
                    "suc": 1 if is_suc else 0,
                    "iter": stat_res[file]["iter"]
                }

    print_res(final_res_dict)


if __name__ == "__main__":
    main(sys.argv)
