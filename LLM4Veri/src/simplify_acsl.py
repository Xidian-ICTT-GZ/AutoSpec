import os, sys, re

# ===== func 'simplify_acsl' start =====
def simplify_acsl(output_std_file_name, merged_file):
    # create a list to store the information of all the failed goals
    fdict_list = []
    # create a list to store the information of all the removed specs
    removed_spec_list = []
    # open the file and read the content into a list
    with open(output_std_file_name, 'r') as f:
        content = f.readlines()
        # iterate over each line in the content list
        for line_index in range(len(content)):
            # if the line contains the goal name, we check if it is a failed goal
            if "file " + merged_file in content[line_index] or "Goal Assigns " in content[line_index]:
                # two flags to indicate if the goal is proved true or proved false
                prove_true_flag = False
                prove_false_flag = False
                # the line index of the current line
                tmp_index = line_index
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
                        try:
                            goal = "Assigns"
                            [(_, linestr, fnstr, linestr2)] = re.findall(r"Goal Assigns (.*), line (.*) in '(.*)' .*: Effect at line (.*)", merged_content)
                        except:
                            try:
                                [(goal, fnstr, linestr)] = re.findall(r"Goal (.*) in '(.*)' .*: Effect at line (.*)", merged_content)
                            except:
                                [(goal, fnstr, linestr)] = re.findall(r"Goal (.*) in (.*): Effect at line (.*)", merged_content)
                    elif "Goal Instance of 'Pre-condition" in content[line_index]:
                        print("\n@@@@@@@@@@@@@@@@@@@@@")
                        print(content[line_index])
                        print("RUNNING simplify_acsl loc 62 branch")
                        break
                    elif "Goal Assertion 'missing_return'" in content[line_index]:
                        print("\n@@@@@@@@@@@@@@@@@@@@@")
                        print(content[line_index])
                        sys.exit(-2)
                    else:
                        [(goal, linestr, fnstr)] = re.findall(r'Goal (.*)\(file .*.c, (.*)\)(.*):', content[line_index])
                    goal = goal.strip()
                    if ")" in linestr:
                        linestr = linestr.split(")")[0]
                    lineint = int(linestr.replace("line ", ""))
                    if fnstr != '' and "in '" in fnstr:
                        fnstr = fnstr.replace("in '", "").replace("'","")
                    # print({"goal": goal, "line": lineint, "fn": fnstr}) # wcventure
                    fdict_list.append({"goal": goal, "line": lineint, "fn": fnstr})
                    
    # if fdict_list's goal are all assign
    all_assign_flag = True
    for i in range(0, len(fdict_list)):
        if not "Assigns " in fdict_list[i]['goal']:
            all_assign_flag = False
        else:
            if fdict_list[i]['goal'] == "Assigns nothing":
                print("2222222222222222222222222")
                removed_spec_list = ["assigns \\nothing;"]
                fdict_list[i]['line'] = 0
                print(fdict_list[i]['line'])
            print(fdict_list)
            #input("33333333333333333333")
    if fdict_list != [] and all_assign_flag == True:
        print(fdict_list)
        #input("44444444444444444444444")
        #input("44444444444444444444444")
        #return -1
    
    # Open the file
    with open(merged_file, 'r') as f:
        # Read the file line by line
        content = f.readlines()
        # For each dictionary in the list of dictionaries
        for each_dict in fdict_list:
            # Replace the line in the file that is specified in the dictionary with a newline
            if "Assigns nothing" in each_dict['goal']:
                for i in range(0, len(content)):
                    if "assigns \\nothing;" in content[i]:
                        content[i] = "//\n"
                        break
            #if "Assigns " in each_dict['goal']:
                #continue
            if each_dict['line'] > 0:
                if content[each_dict['line'] - 1] == "//\n":
                    continue
                removed_spec_list.append(content[each_dict['line'] - 1].strip())
                content[each_dict['line'] - 1] = "//\n"
        
        # remove empty lines
        content = [x for x in content if x != "//\n"]
        
    # write content into new file
    with open(merged_file, 'w') as f:
        f.writelines(content)

    return removed_spec_list
# ===== func 'simplify_acsl' end =====