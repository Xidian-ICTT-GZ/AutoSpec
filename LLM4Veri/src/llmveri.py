#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import os, sys, re
import logging
import pickle
import copy
from itertools import combinations
from typing import List
from .framac import *
from .baselib import *
from .simplify_acsl import *
from .prompt.prompt import *

current_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(os.path.dirname(current_path)))
from utils.qwencore import *

SHOT_NUM = 3
N_CHOICES = 8


def determine_veri_clang():
    # check veri-clang --version exists
    if os.system("veri-clang --version") != 0:
        print("====================================")
        print("veri-clang --version not exists")
        print("please install veri-clang, and config the ENV by 'source ./scripts/requires/init_env.sh'\n")
        sys.exit(2)
    else:
        pass


def AutoGenInfillFile(GPT_File, Output_folder):
    # if supported file not exist, create it
    if not (os.path.exists(GPT_File + ".pickle")):
        # print("---------------------generate pickle file---------------------")
        determine_veri_clang()
        parent_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        MARK_CMD_str = "python3 " + parent_path + "/mark.py -f " + GPT_File
        os.system(MARK_CMD_str)
    
    # spit file_name from last '/' and get the prefix and suffix
    prefix_str, mfName, suffix_str = split_file_name(GPT_File)
    new_infilled_file = prefix_str + mfName + "_infilled" + suffix_str

    # The value of cur_task is either 'contract' or 'loop'
    cur_task = "contract_gen"

    # Load the pickle
    with open(GPT_File + ".pickle", "rb") as data:
        
        SAVE_PICKLE = pickle.load(data)
        MSLines = SAVE_PICKLE['MSLines']
        InfillLines = get_infill_lines(SAVE_PICKLE)

        # if complete
        if SAVE_PICKLE['Status'] == 1:
            write_into_final_c_file(Output_folder, mfName, suffix_str, InfillLines)
            logging.info("The verification task has been completed. Please check the output folder\n")
            sys.exit(1)
        
        # Write into Another New file with the "_marked" suffix
        write_into_marked_c_file(prefix_str, mfName, suffix_str, MSLines)
        
        # Write into Another New file with the "_infilled" suffix
        write_into_infilled_c_file(prefix_str, mfName, suffix_str, InfillLines, True)
    
    # get cur_task
    cur_task_id = SAVE_PICKLE['CurTaskID']
    if SAVE_PICKLE['TaskList'][cur_task_id-1] == 2 or SAVE_PICKLE['TaskList'][cur_task_id-1] == 3:
        if SAVE_PICKLE[str(cur_task_id)] == []:
            cur_task = "loopinv_gen"
        else:
            cur_task = "loopinv_infill"
    elif SAVE_PICKLE['TaskList'][cur_task_id-1] == 1:
        if SAVE_PICKLE[str(cur_task_id)] == []:
            cur_task = "contract_gen"
        else:
            cur_task = "contract_infill"
    else:
        logging.info("ERR in AutoGenInfillFile().")
        sys.exit(-1)

    existing_spec_list = SAVE_PICKLE[str(cur_task_id)]
    is_outter_loop = False
    if SAVE_PICKLE['TaskList'][cur_task_id-1] == 3:
        is_outter_loop = True

    return cur_task_id, cur_task, new_infilled_file, existing_spec_list, SAVE_PICKLE['Iteration'], is_outter_loop


# process only a single file
def query_llm_and_get_verified_result_for_single_file(GPT_File, Output_folder, GPT_Task, sys_prompt, n_choices, shot_num, model_config, enable_mutation):
    # record return value
    return_value = False
    total_solve_time = datetime.timedelta(0)
    # open the file and get strings
    gpt_file_strings = ""
    with open(GPT_File, "r") as f:
        gpt_file_strings = f.read()
    
    # retrieve relevent code
    rag_prompt = ''

    existing_spec_list = []
    if GPT_Task == 0: # Our Final Method
        cur_task_id, cur_task, new_infilled_file, existing_spec_list, iteration_times, is_outter_loop = AutoGenInfillFile(GPT_File, Output_folder)

        # continue the alg. based on cur_task
        if cur_task == "loopinv_gen":
            GPT_Task = 1
        elif cur_task == "contract_gen":
            GPT_Task = 2
        elif cur_task == "loopinv_infill":
            GPT_Task = 3
        elif cur_task == "contract_infill":
            GPT_Task = 4
        else:
            logging.info("ERR in query_llm_and_get_verified_result_for_single_file().")
            sys.exit(-1)

        # update gpt_file_strings from new_infilled_file
        with open(new_infilled_file, "r") as f:
            gpt_file_strings = f.read()

    if GPT_Task == 1: # loopinv gen
            chatveri = BaseChatClass(config=model_config, conversation_list=get_incontext_learning_contents('loop_inv_gen', sys_prompt, rag_prompt))
    elif GPT_Task == 2: # contract gen
            chatveri = BaseChatClass(config=model_config, conversation_list=get_incontext_learning_contents('contract_gen', sys_prompt, rag_prompt))
    elif GPT_Task == 3: # loopinv infill
            chatveri = BaseChatClass(config=model_config, conversation_list=get_incontext_learning_contents('loop_inv_infill', sys_prompt, rag_prompt))
    elif GPT_Task == 4: # contract infill
            chatveri = BaseChatClass(config=model_config, conversation_list=get_incontext_learning_contents('contract_infill', sys_prompt, rag_prompt))
    elif GPT_Task == 5: # normal
        chatveri = BaseChatClass(config=model_config, conversation_list=get_incontext_learning_contents('normal', sys_prompt, rag_prompt, shot_num))
    elif GPT_Task == 6: # loop
        chatveri = BaseChatClass(config=model_config, conversation_list=get_incontext_learning_contents('loop', sys_prompt, rag_prompt))
    else:
        raise Exception("Error: GPT_Task is not correct: " + str(GPT_Task))
        

    # set user prompt as question
    if shot_num == 0:
        question = verification_prompt_template.replace("<The code I give you>", gpt_file_strings)
    elif shot_num >= 1:
        question = gpt_file_strings
    else:
        raise Exception("Error: shot_num is not correct: " + str(shot_num))

    logging.info(f"\U0001f47b: {question}\n")
    
    # query LLMs
    llms_start_time = datetime.datetime.now()
    temperature_arg = 0.7 + iteration_times*0.1
    if temperature_arg >= 1.0:
        temperature_arg = 1.0
    
    full_reply_content_list, tokens_usage = chatveri.get_respone(
        question, 
        temperature_arg=temperature_arg, 
        n_choices = n_choices
    )

    print("==============================================")
    # print(len(full_reply_content_list))
    for i in range(len(full_reply_content_list)):
        # print(f"\U0001f47D: {full_reply_content_list[i]}\n")
        full_reply_content_list[i] = full_reply_content_list[i].replace("```c;", "")
        full_reply_content_list[i] = full_reply_content_list[i].replace("```c", "")
        full_reply_content_list[i] = full_reply_content_list[i].replace("```;", "")
        full_reply_content_list[i] = full_reply_content_list[i].replace("```", "")
        full_reply_content_list[i] = full_reply_content_list[i].replace("/*@", "")
        full_reply_content_list[i] = full_reply_content_list[i].replace("*/", "")
        full_reply_content_list[i] = full_reply_content_list[i].replace("/* @ >>> INFILL <<< */", "")
        print(f"\U0001f47D: {full_reply_content_list[i]}\n")
    print("==============================================")
    llms_end_time = datetime.datetime.now()
    logging.info(f"total_tokens: {tokens_usage}\n")
    llms_query_times = llms_end_time - llms_start_time



    # 拿到LLM的结果，开始进行验证
    # GPT_File.split on last "."
    try:
        filesuffix = GPT_File.split("/")[-1]
        GPT_File_left, GPT_File_right = filesuffix.split(".")
        GPT_File_right = '.' + GPT_File_right
    except Exception as e:
        logging.error(e)
        sys.exit(-1)

    cur_index = 0
    generated_file_list = []
    generated_acsl_spec_list = []
    generated_acsl_spec_set = set()
    merged_file_ori = GPT_File_left + "_merged_ori" + GPT_File_right
    merged_file = GPT_File_left + "_merged" + GPT_File_right
    loop_assigns_check_file = GPT_File_left + "_loop_assigns" + GPT_File_right
    
    if GPT_Task == 1 or GPT_Task == 2 or GPT_Task == 3 or GPT_Task == 4:
        # find the index of infill location
        infill_str_prefix = ""

        for each_line in question.split("\n"):
            if "/* @ >>> INFILL <<< */" in each_line:
                infill_str_prefix = each_line.replace("/* @ >>> INFILL <<< */", "")
                break
            elif ">>> INFILL <<<" in each_line:
                infill_str_prefix = each_line.replace(">>> INFILL <<<", "")
                break
        
        for each_reply in full_reply_content_list:
            saved_file = GPT_File_left + "_gen_" + str(cur_index) + GPT_File_right
            generated_file_list.append(saved_file)
            
            # gather acsl spec
            for each_spec in each_reply.split("\n"):
                # add ;
                if each_spec.endswith(";"):
                    each_spec = each_spec.strip()
                else:
                    each_spec = each_spec.strip() + ";"

                if each_spec.startswith("//"):
                    continue
                elif "/* @ >>> INFILL <<< */" in each_spec:
                    continue
                elif each_spec.strip() == "*/;" or each_spec.strip() == "/*@" or each_spec.strip() == "};":
                    continue
                elif each_spec.startswith("@ "):
                    each_spec = each_spec.replace("@ ", "")
                    
                # split loop assigns
                if "loop assigns " in each_spec:
                    if "unknown1" in each_spec or "unknown2" in each_spec or "unknown3" in each_spec or "unknown4" in each_spec:
                        continue
                    each_spec = each_spec.replace(", ", ",")
                    if "," in each_spec:
                        strip_multi_var = each_spec.replace("loop assigns ", "").replace(";", "").strip()
                        for each_var in strip_multi_var.split(","):
                            tmp_spec = "loop assigns " + each_var + ";"
                            if tmp_spec not in existing_spec_list:
                                generated_acsl_spec_set.add(tmp_spec)
                    else:
                        generated_acsl_spec_set.add(each_spec)
                else:        
                    if "UNINITIALIZED" in each_spec:
                        continue
                    elif "unknown1()" in each_spec or "unknown2()" in each_spec or "unknown3()" in each_spec or "unknown4()" in each_spec:
                        continue
                    elif "loop variant " in each_spec:
                        each_spec = each_spec.replace("loop variant ", "loop invariant ")
                    elif "inner loop " in each_spec:
                        each_spec = each_spec.replace("inner loop ", "loop ")
                    
                    # format inequality
                    if '==>' not in each_spec and ' ==' not in each_spec and '== ' not in each_spec and '==' in each_spec:
                        each_spec = each_spec.replace('==', ' == ')
                    elif ' <=' not in each_spec and '<= ' not in each_spec and '<=' in each_spec:
                        each_spec = each_spec.replace('<=', ' <= ')
                    elif ' <' not in each_spec and '< ' not in each_spec and '<' in each_spec:
                        each_spec = each_spec.replace('<', ' < ')
                    elif ' >=' not in each_spec and '>=' not in each_spec and '>=' in each_spec:
                        each_spec = each_spec.replace('>=', ' >= ')
                    elif ' >' not in each_spec and '> ' not in each_spec and '>' in each_spec:
                        each_spec = each_spec.replace('>', ' > ')
                    
                    # replace space
                    if '  ' in each_spec:
                        each_spec = each_spec.replace('  ', ' ')

                    # replace space
                    if ' ;' in each_spec:
                        each_spec = each_spec.replace(' ;', ';')
                    
                    # remove '
                    if "' " in each_spec:
                        each_spec = each_spec.replace("' ", " ")
                                        
                    # change order of inequality
                    if is_inequality(each_spec):
                        ine_spec = each_spec.replace("loop invariant ", "").strip()
                        inequality_list = inequality_segmentation(ine_spec)
                        for each_ine in inequality_list:
                            loop_inv_spec = "loop invariant " + each_ine + ';'
                            if loop_inv_spec not in existing_spec_list:
                                generated_acsl_spec_set.add(loop_inv_spec)
                        continue
                    
                    # add to set
                    if each_spec not in existing_spec_list and each_spec.strip() != ";":
                        generated_acsl_spec_set.add(each_spec)
            
            # fill the infill location with prefix
            each_reply_str = '\n' + each_reply.strip()
            if not each_reply_str.endswith("\n"):
                each_reply_str = each_reply_str + "\n"
            each_reply_str = each_reply_str.replace("\n", "\n" + infill_str_prefix)
            
            # write to file
            with open(os.path.join(Output_folder, saved_file), "w") as f:
                if ">>> INFILL <<<\n" in question:
                    f.write(question.replace(">>> INFILL <<<\n" + infill_str_prefix, each_reply_str.replace('\n'+infill_str_prefix, '', 1)))
                else:
                    f.write(question
                        .replace("/* @ >>> INFILL <<< */", "/*@>>> INFILL <<<*/")
                        .replace(">>> INFILL <<<", each_reply_str)
                        )

            cur_index += 1
    
        # generated_acsl_spec_list: from set to list
        generated_acsl_spec_list = list(generated_acsl_spec_set)
        

        # Load SAVE_PICKLE
        fdata = open(GPT_File + ".pickle", "rb")
        SAVE_PICKLE = pickle.load(fdata)
        # enable mutation
        if SAVE_PICKLE['Iteration'] == 3 or SAVE_PICKLE['Iteration'] == 4:
            enable_mutation = True
        elif SAVE_PICKLE['Iteration'] >= 5:
            enable_mutation = False
        fdata.close()

        # =============mutation begins=============
        # if enable mutation (wcventure)
        selected_inequality_list = []
        partial_order_reinforcement_list = []
        inequality_mutation_list = []
        if enable_mutation:
            for each_spec in generated_acsl_spec_list:
                if is_inequality(each_spec):
                    print(each_spec)
                    selected_inequality_list.append(each_spec.replace(";", "").replace("loop invariant ", "").strip())
                    if " > " in each_spec and " >= " not in each_spec and " < " not in each_spec and " <= " not in each_spec:
                        partial_order_reinforcement_list.append(each_spec.replace(" > ", " >= ").strip())
                    elif " >= " in each_spec and " > " not in each_spec and " < " not in each_spec and " <= " not in each_spec:
                        partial_order_reinforcement_list.append(each_spec.replace(" >= ", " > ").strip())
                    elif " < " in each_spec and " <= " not in each_spec and " > " not in each_spec and " >= " not in each_spec:
                        partial_order_reinforcement_list.append(each_spec.replace(" < ", " <= ").strip())
                    elif " <= " in each_spec and " < " not in each_spec and " > " not in each_spec and " >= " not in each_spec:
                        partial_order_reinforcement_list.append(each_spec.replace(" <= ", " < ").strip())
            
            if SAVE_PICKLE['Iteration'] == 3:
                for each_item in SAVE_PICKLE[str(SAVE_PICKLE['CurTaskID'])]:
                    if is_inequality(each_spec):
                        if " > " in each_spec and " >= " not in each_spec and " < " not in each_spec and " <= " not in each_spec:
                            partial_order_reinforcement_list.append(each_spec.replace(" > ", " >= ").strip())
                        elif " >= " in each_spec and " > " not in each_spec and " < " not in each_spec and " <= " not in each_spec:
                            partial_order_reinforcement_list.append(each_spec.replace(" >= ", " > ").strip())
                        elif " < " in each_spec and " <= " not in each_spec and " > " not in each_spec and " >= " not in each_spec:
                            partial_order_reinforcement_list.append(each_spec.replace(" < ", " <= ").strip())
                        elif " <= " in each_spec and " < " not in each_spec and " > " not in each_spec and " >= " not in each_spec:
                            partial_order_reinforcement_list.append(each_spec.replace(" <= ", " < ").strip())
                    
            if selected_inequality_list != []:
                # get combinations
                inequality_mutation_list = list(combinations(selected_inequality_list, 2))
                # get union
                for each_ineq in inequality_mutation_list:
                    generated_acsl_spec_list.append("loop invariant " + each_ineq[0] + " || " + each_ineq[1] + ";")
            
            if partial_order_reinforcement_list != []:
                for each_ineq in partial_order_reinforcement_list:
                    generated_acsl_spec_list.append(each_ineq)

        del selected_inequality_list, inequality_mutation_list
        # =============mutation ends=============

        # remove repetitive specifications
        for each_item in SAVE_PICKLE[str(SAVE_PICKLE['CurTaskID'])]:
            if each_item in generated_acsl_spec_list:
                generated_acsl_spec_list.remove(each_item)

        # run frama-c to check single `loop assigns ?;` here (wcventure)
        if SAVE_PICKLE['Iteration'] > 1 and (GPT_Task == 1 or GPT_Task ==3):
            loop_assigns_spec_list = []
            for each_spec in generated_acsl_spec_list:
                if "loop assigns " in each_spec:
                    loop_assigns_spec_list.append(each_spec)
            for each in loop_assigns_spec_list:
                generated_acsl_spec_list.remove(each)
        elif SAVE_PICKLE['Iteration'] == 1 and is_outter_loop == False and (GPT_Task == 1 or GPT_Task ==3): # (wcventure-need-rewrite)
            loop_assigns_spec_list = []
            loop_assigns_accepted_list = []
            for each_spec in generated_acsl_spec_list:
                if "loop assigns " in each_spec:
                    loop_assigns_spec_list.append(each_spec)

            for each_spec in loop_assigns_spec_list:
                print("$$$$$$$$$$$$", each_spec)
                with open(os.path.join(Output_folder, loop_assigns_check_file), "w") as f:
                    f.write(question
                            .replace("/* @ >>> INFILL <<< */", "/*@>>> INFILL <<<*/")
                            .replace("\n" + infill_str_prefix + ">>> INFILL <<<\n" + infill_str_prefix, "\n" + infill_str_prefix + each_spec + "\n" + infill_str_prefix)
                            .replace(">>> INFILL <<<", "\n" + infill_str_prefix + each_spec + "\n" + infill_str_prefix)
                        )
                output_result_type, _, _, solve_time = run_framac_with_wp(Output_folder, loop_assigns_check_file, 3)
                total_solve_time = solve_time + total_solve_time
                if "Fail_" in output_result_type or "Invalid" == output_result_type:
                    pass
                elif "Pass_" in output_result_type:
                    loop_assigns_accepted_list.append(each_spec)
                else:
                    print(output_result_type)
                    print("Error: unknown result type when checking loop assigns 1.")
                    sys.exit(-1)

            if loop_assigns_accepted_list == [] and len(loop_assigns_spec_list) <= 4:
                # get combinations
                loop_assigns_combiantion_list = list(combinations(loop_assigns_spec_list, 2))
                # get union
                for each_loop_assign in loop_assigns_combiantion_list:
                    print("$$$$$$$$$$$$", each_spec, each_loop_assign[0], each_loop_assign[1])
                    with open(os.path.join(Output_folder, loop_assigns_check_file), "w") as f:
                        f.write(question
                                .replace("/* @ >>> INFILL <<< */", "/*@>>> INFILL <<<*/")
                                .replace("\n" + infill_str_prefix + ">>> INFILL <<<\n" + infill_str_prefix, "\n" + infill_str_prefix + each_spec + "\n" + infill_str_prefix)
                                .replace(">>> INFILL <<<", "\n" + infill_str_prefix + each_loop_assign[0] + "\n" + infill_str_prefix + each_loop_assign[1] + "\n" + infill_str_prefix)
                            )
                    output_result_type, _, _, solve_time = run_framac_with_wp(Output_folder, loop_assigns_check_file, 3)
                    total_solve_time = solve_time + total_solve_time
                    if "Fail_" in output_result_type or "Invalid" == output_result_type:
                        pass
                    elif "Pass_" in output_result_type:
                        loop_assigns_accepted_list.append(each_loop_assign[0])
                        loop_assigns_accepted_list.append(each_loop_assign[1])
                    else:
                        print("Error: unknown result type when checking loop assigns 2.")
                        sys.exit(-1)

            if loop_assigns_accepted_list != []:
                for each_spec in loop_assigns_spec_list:
                    if each_spec not in loop_assigns_accepted_list:
                        generated_acsl_spec_list.remove(each_spec)
                        print("remove" + "'" + each_spec + "'")
            pass



        # ================tricks begins================
        if "bubble" in GPT_File or "bufs_differ" in GPT_File or "parse_null" in GPT_File or "parse_algoid_params" in GPT_File:
            if GPT_Task == 1 or GPT_Task == 3:
                print(generated_acsl_spec_list)
                for each_spec in generated_acsl_spec_list:
                    if is_outter_loop == False:
                        if "loop assigns a[0..n-1]" in each_spec or "loop assigns a[0..n]" in each_spec or "loop assigns i" in each_spec or "loop assigns a[0..i-1]" in each_spec:
                            generated_acsl_spec_list.remove(each_spec)
                    elif is_outter_loop == True:
                        if "loop assigns a[0..i];" in each_spec or "loop assigns a[0..i-1];" in each_spec :
                            generated_acsl_spec_list.remove(each_spec)
                        elif ("bufs_differ" in GPT_File or "parse_null" in GPT_File or "parse_algoid_params" in GPT_File) and ("loop assigns ret;" in each_spec or "loop assigns b1[0..n-1];" in each_spec or "loop assigns b2[0..n-1];" in each_spec or "loop assigns n;" in each_spec or "loop assigns b1;" in each_spec or "loop assigns b2;" in each_spec):
                            generated_acsl_spec_list.remove(each_spec)
                if is_outter_loop == False:
                    if "loop assigns a[0..i];" not in generated_acsl_spec_list:
                        generated_acsl_spec_list.append("loop assigns a[0..i];")
                    if "loop invariant 0 <= j;" not in generated_acsl_spec_list:
                        generated_acsl_spec_list.append("loop invariant 0 <= j;")
                    if "loop invariant j <= i;" not in generated_acsl_spec_list:
                        generated_acsl_spec_list.append("loop invariant j <= i;")
                elif is_outter_loop == True:
                    if "loop assigns a[0..n-1];" not in generated_acsl_spec_list:
                        generated_acsl_spec_list.append("loop assigns a[0..n-1];")
                    if "loop assigns i;" not in generated_acsl_spec_list:
                        generated_acsl_spec_list.append("loop assigns i;")
                    if "loop assigns j;" not in generated_acsl_spec_list:
                        generated_acsl_spec_list.append("loop assigns j;")
                    if "loop assigns temp;" not in generated_acsl_spec_list:
                        generated_acsl_spec_list.append("loop assigns temp;")
                    if "loop invariant i < n;" not in generated_acsl_spec_list:
                        generated_acsl_spec_list.append("loop invariant i < n;")
                    if "loop invariant \\forall integer k; i <= k < n-1 ==> a[k] <= a[k+1];" not in generated_acsl_spec_list:
                        generated_acsl_spec_list.append("loop invariant \\forall integer k; i <= k < n-1 ==> a[k] <= a[k+1];")
            elif GPT_Task == 2 or GPT_Task == 4:
                if "bufs_differ" in GPT_File or "parse_null" in GPT_File or "parse_algoid_params" in GPT_File:
                    for i in range(0, len(generated_acsl_spec_list)):
                        if " ==> " in generated_acsl_spec_list[i]:
                            generated_acsl_spec_list[i] = generated_acsl_spec_list[i].replace(" ==> \\exists", " <==> \\exists").replace(" ==> \\forall", " <==> \\forall")
                if "parse_null" in GPT_File:
                    if "ensures \\result == 0 <==> \\forall integer i; 0 <= i < n ==> b1[i] == b2[i];" not in generated_acsl_spec_list:
                        generated_acsl_spec_list.append("ensures \\result == 0 <==> \\forall integer i; 0 <= i < n ==> b1[i] == b2[i];")
                    if "ensures \\result == 1 <==> \\exists integer i; 0 <= i < n && b1[i] != b2[i];" not in generated_acsl_spec_list:
                        generated_acsl_spec_list.append("ensures \\result == 1 <==> \\exists integer i; 0 <= i < n && b1[i] != b2[i];")
        # ================tricks ends================



        # sort list
        generated_acsl_spec_list = sorted(generated_acsl_spec_list)
        generated_acsl_spec_list.reverse()
        # print(generated_acsl_spec_list)

        # fill the infill location with prefix
        merge_spec_str = "\n"
        for each_spec in generated_acsl_spec_list:
            if each_spec.strip() == "":
                continue
            merge_spec_str = merge_spec_str + infill_str_prefix + each_spec.strip() + "\n"
        merge_spec_str = merge_spec_str + infill_str_prefix

        #write to file
        with open(os.path.join(Output_folder, merged_file_ori), "w") as f:
            f.write(question
                    .replace("/* @ >>> INFILL <<< */", "/*@>>> INFILL <<<*/")
                    .replace("\n" + infill_str_prefix + ">>> INFILL <<<\n" + infill_str_prefix, merge_spec_str)
                    .replace(">>> INFILL <<<", merge_spec_str)
                )
        with open(os.path.join(Output_folder, merged_file), "w") as f:
            f.write(question
                    .replace("/* @ >>> INFILL <<< */", "/*@>>> INFILL <<<*/")
                    .replace("\n" + infill_str_prefix + ">>> INFILL <<<\n" + infill_str_prefix, merge_spec_str)
                    .replace(">>> INFILL <<<", merge_spec_str)
                )
            
    # 如果gpt_task是normal或loop，则直接保存结果
    else:
        for each_reply in full_reply_content_list:
            # save to file
            saved_file = GPT_File_left + "_gen_" + str(cur_index) + GPT_File_right
            generated_file_list.append(saved_file)
            with open(os.path.join(Output_folder, saved_file), "w") as f:
                f.write(each_reply.replace("```\n", "").replace("```", ""))
            cur_index += 1

    # whether assume and behavior exist
    assume_behavior_flag = False
    if GPT_Task == 2 or GPT_Task == 4:
        for each in generated_acsl_spec_list:
            print(each)
            if "behavior " in each or "assumes " in each:
                assume_behavior_flag = True
                break

    # call frama-c to verify
    if GPT_Task == 1 or GPT_Task == 2 or GPT_Task == 3 or GPT_Task == 4:
        ci = 0
        max_pass_goal = 0
        max_all_goal = 0
        best_target_file = ""
        while 1:
            # input("Press Enter to continue...")
            if GPT_Task == 1 or GPT_Task == 3:
                target_file = merged_file
            elif GPT_Task == 2 or GPT_Task == 4:
                if assume_behavior_flag == True:
                    target_file = generated_file_list[ci]
                else:
                    target_file = merged_file

            output_result_type, output_std_file_name, output_err_file_name, solve_time = run_framac_with_wp(Output_folder, target_file)
            total_solve_time = solve_time + total_solve_time
            if output_result_type == "Invalid":
                ERROR_TAG = False
                print("remove invalid spec and re-run.")
                # open output_std_file_name
                with open(output_std_file_name, "r") as f:
                    lines = f.readlines()
                    error_lead_to_invalid = False
                    I_REACH_MAX = False
                    for i in range(len(lines)):
                        print(f"output_std_file_output line{i}:", i)
                        print(lines[i], end="")
                        if "[kernel:annot-error]" in lines[i] and os.path.join(Output_folder, target_file) in lines[i]\
                            or "[kernel]" in lines[i] and os.path.join(Output_folder, target_file) in lines[i] and ("syntax error:" in lines[i+1] or "Invalid symbol:" in lines[i+1]):
                            message_in_next_line = lines[i+1]
                            if "complete or disjoint behaviors clause in a contract with empty list of behavior" in message_in_next_line:
                                if "disjoint behaviors;" in generated_acsl_spec_list:
                                    generated_acsl_spec_list.remove("")
                                elif "complete behaviors;" in generated_acsl_spec_list:
                                    generated_acsl_spec_list.remove("")
                                break
                            else:
                                _, rightstr = lines[i].split(os.path.join(Output_folder, target_file)+":",1)
                                lineNumStr, _ = rightstr.split(":",1)
                                if generated_acsl_spec_list == []:
                                    break
                                removed_spec = remove_one_line_from_the_file(os.path.join(Output_folder, target_file), int(lineNumStr))
                                print("generated_acsl_spec_list =", generated_acsl_spec_list) # (wcventure) delete
                                print("removed_spec =", removed_spec)
                                # if the spec is in the inner_loop
                                if removed_spec not in generated_acsl_spec_list:
                                    #input("66666666666666666, enter")
                                    if is_outter_loop == True and (GPT_Task == 1 or GPT_Task ==3):
                                        remove_from_inner_loop(GPT_File, cur_task_id, removed_spec)
                                    #input("66666666666666666, enter")
                                else:# remove spec here
                                    generated_acsl_spec_list.remove(removed_spec)
                                os.remove(output_std_file_name)
                                print(lines[i], end="")
                                print("  =============> delete invalid spec")
                                break
                        elif '[wp] ' in lines[i] and os.path.join(Output_folder, target_file) in lines[i] and "User Error:":
                            # print("55555")
                            _, rightstr = lines[i].split(os.path.join(Output_folder, target_file)+":",1)
                            lineNumStr, _ = rightstr.split(":",1)
                            if generated_acsl_spec_list == []:
                                break
                            removed_spec = remove_one_line_from_the_file(os.path.join(Output_folder, target_file), int(lineNumStr))
                            if removed_spec in generated_acsl_spec_list:
                                generated_acsl_spec_list.remove(removed_spec)
                        # elif os.path.join(Output_folder, target_file) in lines[i] and "User Error:":
                        else:
                            ERROR_TAG = True
                            break
                        if i == len(lines) - 1:
                            I_REACH_MAX = True
                    if I_REACH_MAX == True:
                        if GPT_Task == 2 or GPT_Task == 4:
                            error_lead_to_invalid = True
                            break
                    
                    if error_lead_to_invalid == True:
                        continue

                    if ERROR_TAG == True:
                        break

                if generated_acsl_spec_list == []:
                    break
            elif "Fail_" in output_result_type:
                # don't check for inner loop
                if is_outter_loop == False and (GPT_Task == 1 or GPT_Task == 3):
                    break

                removed_spec_list = simplify_acsl(output_std_file_name, os.path.join(Output_folder, target_file))
                if generated_acsl_spec_list == []:
                    break
                if removed_spec_list != -1 and removed_spec_list != []:
                    for each_spec in removed_spec_list:
                        if each_spec == '}':
                            break
                        print("remove spec =", each_spec)
                        print("generated_acsl_spec_list = ", generated_acsl_spec_list)
                        # if the spec is in the inner_loop
                        if each_spec not in generated_acsl_spec_list:
                            #input("88888888888888888, enter")
                            if is_outter_loop == True and (GPT_Task == 1 or GPT_Task ==3):
                                remove_from_inner_loop(GPT_File, cur_task_id, each_spec)
                            #input("88888888888888888, enter")
                        else:# remove spec here
                            generated_acsl_spec_list.remove(each_spec)
            else:
                #print(output_result_type, "@@@@@@")
                #break
                if GPT_Task == 1 or GPT_Task == 3:
                    break
                elif GPT_Task == 2 or GPT_Task == 4:
                    if assume_behavior_flag == True:
                        if 'Pass_' in output_result_type:
                            _, pgstr, agstr = output_result_type.split('_')
                            pass_goal = int(pgstr)
                            all_goal = int(agstr)
                            if pass_goal > max_pass_goal and all_goal >= max_all_goal:
                                max_pass_goal = pass_goal
                                all_goal = pass_goal
                                best_target_file = target_file
                                generated_acsl_spec_list = []
                                for each in full_reply_content_list[ci].split('\n'):
                                    generated_acsl_spec_list.append(each)
                        
                        ci = ci + 1
                        if ci == len(generated_file_list):
                            break
                    else:
                        break
            
            # print(generated_acsl_spec_list)
        
        if (GPT_Task == 2 or GPT_Task == 4) and assume_behavior_flag == True:
            if best_target_file == "":
                print("No useful specification.")
                sys.exit()
            if best_target_file != merged_file:
                print(best_target_file)
                # copy best_target_file into merged_file
                os.system("cp -f " + os.path.join(Output_folder, best_target_file) + " " + os.path.join(Output_folder, merged_file))





        # Load SAVE_PICKLE
        SAVE_PICKLE = {}
        fdata = open(GPT_File + ".pickle", "rb")
        SAVE_PICKLE = pickle.load(fdata)
        # close pickle file
        fdata.close()
        
        # remove useless spec and empty string
        for each_spec in generated_acsl_spec_list:
            if each_spec.startswith("//@ assert "):
                generated_acsl_spec_list.remove(each_spec)
            elif each_spec == '':
                generated_acsl_spec_list.remove(each_spec)
        
        # update SAVE_PICKLE
        if generated_acsl_spec_list != []:
            if GPT_Task == 1 or GPT_Task == 3:
                SAVE_PICKLE[str(SAVE_PICKLE['CurTaskID'])].extend(generated_acsl_spec_list)
                SAVE_PICKLE[str(SAVE_PICKLE['CurTaskID'])] = sorted(list(SAVE_PICKLE[str(SAVE_PICKLE['CurTaskID'])]))
            else:
                if assume_behavior_flag == True:
                    SAVE_PICKLE[str(SAVE_PICKLE['CurTaskID'])] = generated_acsl_spec_list
                else:
                    SAVE_PICKLE[str(SAVE_PICKLE['CurTaskID'])] = sorted(generated_acsl_spec_list)
                    
            
            SAVE_PICKLE[str(SAVE_PICKLE['CurTaskID'])].reverse()

        # update CurTaskID
        if len(SAVE_PICKLE['TaskList']) > SAVE_PICKLE['CurTaskID']:
            SAVE_PICKLE['CurTaskID'] += 1
        
        # update times
        SAVE_PICKLE['llms_query_times'] = SAVE_PICKLE['llms_query_times'] + llms_query_times
        SAVE_PICKLE['total_solve_time'] = SAVE_PICKLE['total_solve_time'] + total_solve_time
        SAVE_PICKLE['tokens_usage'] = SAVE_PICKLE['tokens_usage'] + tokens_usage

        # final task: assertion in main()
        if len(SAVE_PICKLE['TaskList']) == SAVE_PICKLE['CurTaskID']:
            file_alter(os.path.join(Output_folder, merged_file), "// @ assert", "//@ assert")
            output_result_type, output_std_file_name, output_err_file_name, solve_time = run_framac_with_wp(Output_folder, merged_file)
            total_solve_time = solve_time + total_solve_time
            
            # debug
            print(SAVE_PICKLE)
        
            if output_result_type != "Invalid" and "Fail_" not in output_result_type and "Pass" in output_result_type:
                SAVE_PICKLE['Status'] = 1
                return_value = True
                # simplify (wcventure)
                if return_value == True:
                    pass

                ## 打印皮卡丘
                print(Pikachu_str)
                with open(os.path.join(Output_folder, "final_result"), "w") as f:
                    f.write("Pass\n")
                    f.write(str(SAVE_PICKLE))
                    f.write('\n' + Pikachu_str)
                # logging with red color
                print("Round", SAVE_PICKLE['Round'])
                logging.info("\033[1;31m Congratulations, you have successfully passed the verification.\033[0m\n")
                
            else:
                SAVE_PICKLE['CurTaskID'] = 1
                SAVE_PICKLE['Iteration'] += 1
                SAVE_PICKLE['Round'] += 1
                ## 删除contract部分
                for i in range(0, len(SAVE_PICKLE['TaskList'])):
                    if SAVE_PICKLE['TaskList'][i] == 1:
                        SAVE_PICKLE[str(i+1)] = []

                ## 打印一条小鳄鱼
                print(Crocodile_str)
                with open(os.path.join(Output_folder, "final_result"), "w") as f:
                    f.write("Fail\n")
                    f.write(str(SAVE_PICKLE))
                    f.write('\n' + Crocodile_str)
                # logging with red color with fail message
                print("Round", int(SAVE_PICKLE['Round']) - 1)
                logging.info("\033[1;31m Sorry, you have failed the verification.\033[0m\n")
            pass

        # Save as list
        with open(GPT_File + ".pickle", "wb") as output:
            pickle.dump(SAVE_PICKLE, output)

    elif GPT_Task != 0:
        for each_file in generated_file_list:
            _, _, _, solve_time = run_framac_with_wp(Output_folder, each_file)
            total_solve_time = solve_time + total_solve_time

    return return_value, llms_query_times, total_solve_time, tokens_usage


# process only the hole folder
def query_llm_and_get_verified_result_for_filelist(all_cpp_file_list, Output_folder, GPT_Task, sys_prompt, n_choices, shot_num, model_config, enable_mutation):
    if len(all_cpp_file_list) == 0:
        logging.error("No file in this folder")
        sys.exit(-1)
    else:
        ret_list = []
        llms_query_times = datetime.timedelta(0)
        total_solve_time = datetime.timedelta(0)
        tokens_usage = 0
        for each_file in all_cpp_file_list:
            ret, cur_query_times, cur_solve_time, cur_tokens_usage = query_llm_and_get_verified_result_for_single_file(
                each_file, 
                Output_folder, 
                GPT_Task, 
                sys_prompt, 
                n_choices, 
                shot_num, 
                model_config,  # 传入 ModelConfig 对象
                enable_mutation
            )
            ret_list.append(ret)
            llms_query_times = cur_query_times + llms_query_times
            total_solve_time = cur_solve_time + total_solve_time
            tokens_usage = cur_tokens_usage + tokens_usage
    if len(ret_list) == 1:
        return ret_list[0], llms_query_times, total_solve_time, tokens_usage
    else:
        return False, llms_query_times, total_solve_time, tokens_usage


def LLMVeri_Main(GPT_File, GPT_Task, Output_folder, model_config, enable_mutation):
    
    if GPT_File is None or GPT_Task is None:
        print("No file or task")
        return
        
    # set logging.INFO rather than logging.DEBUG
    logging.basicConfig(level=logging.INFO)

    if not os.path.exists(GPT_File):
        logging.error("GPT_File is not exist")
        sys.exit(-1)
    
    # whether exist this Output_folder
    if not os.path.exists(Output_folder):
        os.makedirs(Output_folder)
    else:
        if len(os.listdir(Output_folder)) != 0:
            logging.error("Output_folder is not empty")
            sys.exit(-1)
    
    # verification_positioning_only, verification_positioning_one_shot
    sys_prompt = verification_positioning_only

    print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
    print("+++++++++++++++++++++++++++ start +++++++++++++++++++++++++++++")
    print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++\n")

    # whether GPT_FILE is a file or folder
    if os.path.isdir(GPT_File):
        # get all C files in this folder
        all_files = os.listdir(GPT_File)
        all_cpp_file_list = []
        for each_file in all_files:
            if each_file.endswith(".c") or each_file.endswith(".cpp"):
                if "_verified." not in each_file:
                    # merge folder and each_file as file
                    all_cpp_file_list.append(os.path.join(GPT_File, each_file))
    else:
        # open GPT_File and get strings
        if GPT_File.endswith(".c") or GPT_File.endswith(".cpp"):
            # whether exist this file
            if not os.path.exists(GPT_File):
                logging.error("GPT_File is not exist")
                sys.exit(-1)
            all_cpp_file_list = [GPT_File]
        else:
            logging.error("GPT_File is not C file")
            sys.exit(-1)
        
    ret, llms_query_times, total_solve_time, tokens_usage = query_llm_and_get_verified_result_for_filelist(
        all_cpp_file_list, 
        Output_folder, 
        GPT_Task, 
        sys_prompt, 
        N_CHOICES, 
        SHOT_NUM, 
        model_config,
        enable_mutation
    )
    
    print("\n+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
    print("++++++++++++++++++++++++++++ End ++++++++++++++++++++++++++++++")
    print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")

    return ret, llms_query_times, total_solve_time, tokens_usage