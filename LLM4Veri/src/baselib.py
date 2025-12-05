#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import os, sys
import re
import pickle

current_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(os.path.dirname(current_path)))
# from conf.jsoninfo import *

CONST_DEBUG = 1 # 0 or 1

Pikachu_str = """\
    へ　　　　　／|
　　/＼7　　　 ∠＿/
　 /　│　　 ／　／
　│　Z ＿,＜　／　　 /`ヽ
　│　　　　　ヽ　　 /　　〉
　 Y　　　　　`　 /　　/
　ｲ●　､　●　　⊂⊃〈　　/
　()　 へ　　　　|　＼〈
　　>ｰ ､_　 ィ　 │ ／／
　 / へ　　 /　ﾉ＜| ＼＼
　 ヽ_ﾉ　　(_／　 │／／
　　7　　　　　　　|／
　　＞―r￣￣`ｰ―＿
"""

Crocodile_str = """\
                  __  __
      _ _        /_@>_@> \          /^^\ /^\ /^^\_ 
    _/oo \____/~''. . .  '~\       /'\''  ~ ''~~' -'\_ 
   / '.'. ~.~.~.       .'    ~ |     /'\~~..''''.'' ''  ~\_ 
  <'_'_'_'_'_'_'_'_  ' :   '     \_/' '.''  . '.   .''  '.  ~\_ 
             ~V~V~V~V  \   ~\  '' '~  '   '' ~   `   ~  ''   ~\_ 
    /\~/\~/\~/\~/|/  '   ''  _   ' ~ ''  '    ~  '' __  '  ..  \_ 
 <-- --- ---.---.--/'   ''   /'  '\_ '' ': ~ ;;''    ' /''; \ ;'''''' '' ~\ _ 
    \~ '. . : .:: ~. :.  /_'''_'' \_' :'''_ : _ ''/''_' '_ \:_ '''' #''..\/\/\/~/\~ ''~~~~~O
 ~~ \-~ `---~~~---- \<_><_><_>/ ~ ~~' ~\<_><_><_>\_~_~_~_~_~/˜¤¹
"""

def file_alter(file, old_str, new_str):
    """
    替换文件中的字符串
    :param file:文件名
    :param old_str:就字符串
    :param new_str:新字符串
    :return:
    """
    file_data = ""
    with open(file, "r", encoding="utf-8") as f:
        for line in f:
            if old_str in line:
                line = line.replace(old_str,new_str)
            file_data += line
    with open(file,"w",encoding="utf-8") as f:
        f.write(file_data)
 

def split_file_name(file_name):
    prefix_str = ""
    suffix_str = ""
    mfName = ""

    if '/' in file_name:
        print("[DEBUG] target file name = ", file_name)
        prefix_str, suffix_str = file_name.rsplit('/', 1)
        prefix_str = prefix_str + '/'
    else:
        suffix_str = file_name
    
    if '.' in suffix_str:
        mfName, suffix_str = suffix_str.rsplit('.', 1)
        suffix_str = '.' + suffix_str

    # print("prefix_str: ", prefix_str, "\nmfName: ", mfName, "\nsuffix_str: ", suffix_str)
    return prefix_str, mfName, suffix_str


def is_inequality(str_input):
    if "loop invariant " in str_input and \
        "||" not in str_input and \
        "&&" not in str_input and \
        '==>' not in str_input and \
        '==' not in str_input and \
        str_input.count(' > ') + str_input.count(' >= ') + str_input.count(' < ') + str_input.count(' <= ') >= 1:
        return True
    else:
        return False


def auto_naming_output_folder(pointed_output_file, gpt_file, is_simplified = False):
    if pointed_output_file == "":
        if not os.path.exists('out'):
            os.makedirs('out')
        pointed_output_file = 'out/'
    else:
        if not os.path.exists(pointed_output_file):
            os.makedirs(pointed_output_file)
        pointed_output_file = pointed_output_file + '/'
    
    output_folder = ""
    _, mfName, _ = split_file_name(gpt_file)
    for i in range(1, 10000):
        # format i to 000x
        index = ""
        last_index = ""
        if i < 10:
            index = '000' + str(i)
            last_index = '000' + str(i-1)
        elif i < 100:
            index = '00' + str(i)
            if i != 10:
                last_index = '00' + str(i-1)
            else:
                last_index = '000' + str(i-1)
        elif i < 1000:
            index = '0' + str(i)
            if i != 100:
                last_index = '0' + str(i-1)
            else:
                last_index = '00' + str(i-1)
        else:
            index = str(i)
            if i != 1000:
                last_index = str(i-1)
            else:
                last_index = '0' + str(i-1)

        if os.path.exists(pointed_output_file + mfName + '_' + index) and os.listdir(pointed_output_file + mfName + '_' + index) == []:
            if is_simplified == False:
                output_folder = pointed_output_file + mfName + '_' + index
            else:
                output_folder = pointed_output_file + mfName + '_' + last_index + '_simplified'
            break
        elif not os.path.exists(pointed_output_file + mfName + '_' + index):
            if is_simplified == False:
                output_folder = pointed_output_file + mfName + '_' + index
            else:
                output_folder = pointed_output_file + mfName + '_' + last_index + '_simplified'
            break
    
    return output_folder


def get_infill_lines(SAVE_PICKLE):
    cur_task_id = SAVE_PICKLE['CurTaskID']
    InfillLines = SAVE_PICKLE['MSLines'].copy()

    if CONST_DEBUG == 1:
        print(SAVE_PICKLE)
    
    for i in range(0, len(InfillLines)):
        RE_MATCH_CONTRACT = re.match(r'\s*\/\* (\d+). FUNC CONTRACT \*\/*', InfillLines[i])
        RE_MATCH_INVARIANT = re.match(r'\s*\/\* (\d+). LOOP INVARIANT \*\/*', InfillLines[i])
        if RE_MATCH_CONTRACT or RE_MATCH_INVARIANT:
            if RE_MATCH_CONTRACT:
                this_task_id = RE_MATCH_CONTRACT.group(1)
            elif RE_MATCH_INVARIANT:
                this_task_id = RE_MATCH_INVARIANT.group(1)
            
            if int(this_task_id) == int(cur_task_id):
                # add INFILL
                indx = InfillLines[i].find("*/")
                # get Space character prefix
                space_prefix = re.match(r'\s*', InfillLines[i]).group()
                # if loop task
                if SAVE_PICKLE[str(this_task_id)] != [] and SAVE_PICKLE['TaskList'][int(this_task_id)-1]:
                    exists_contract = space_prefix + "/*@\n" + space_prefix + ">>> INFILL <<<\n"
                    for each_spec in SAVE_PICKLE[str(this_task_id)]:
                        exists_contract = exists_contract + space_prefix + each_spec + '\n'
                    InfillLines[i] = exists_contract + space_prefix + '*/\n' + InfillLines[i][indx+3:]
                else:
                    InfillLines[i] = space_prefix + "/* @ >>> INFILL <<< */\n" + InfillLines[i][indx+3:]
            else:
                # remove FUNC CONTRACT and LOOP INVARIANT
                indx = InfillLines[i].find("*/")
                InfillLines[i] = InfillLines[i][indx+3:]
                # if there exists proved specification
                if str(this_task_id) in SAVE_PICKLE:
                    if SAVE_PICKLE[str(this_task_id)] != []:
                        # get Space character prefix
                        space_prefix = re.match(r'\s*', InfillLines[i]).group()
                        inserted_spec = space_prefix + "/*@\n"
                        for each_spec in SAVE_PICKLE[str(this_task_id)]:
                            inserted_spec = inserted_spec + space_prefix + each_spec + '\n'
                        InfillLines[i] = inserted_spec + space_prefix + '*/\n' +  InfillLines[i]
                    else:
                        pass
                else:
                    pass

    if CONST_DEBUG == 1:
        print("")
        for each in InfillLines:
            print(each, end="")
        print("\n---------------------------------\n")
    #sys.exit(2)
    return InfillLines


def remove_from_inner_loop(GPT_File, cur_task_id, removed_spec):
    SAVE_PICKLE = {}
    with open(GPT_File + ".pickle", "rb") as fdata:
        SAVE_PICKLE = pickle.load(fdata)
        previous_task_id = cur_task_id-1
        while previous_task_id >=0:
            if SAVE_PICKLE['TaskList'][previous_task_id-1] == 2: # inner loop
                if removed_spec in SAVE_PICKLE[str(previous_task_id)]:
                    SAVE_PICKLE[str(previous_task_id)].remove(removed_spec)
                    break
                else:
                    if previous_task_id == 0:
                        print("ERR in remove spec in inner loop 1")
                        sys.exit(-1)
                    previous_task_id -= 1
                    continue
            else:
                #print("ERR in remove spec in inner loop 2")
                #sys.exit(-1)
                break
                
    # save & dump
    with open(GPT_File + ".pickle", "wb") as fdata:
        pickle.dump(SAVE_PICKLE, fdata)


def write_into_marked_c_file(prefix_str, mfName, suffix_str, MSLines):
    # Write into Another New file with the "_marked" suffix
    with open(prefix_str + mfName + "_marked" + suffix_str, 'w') as f:
        f.writelines(MSLines)


def write_into_infilled_c_file(prefix_str, mfName, suffix_str, InfillLines, filt_assert = True):
    # Write into Another New file with the "_infilled" suffix
    with open(prefix_str + mfName + "_infilled" + suffix_str, 'w') as f:
        remove_assert_Lines = InfillLines.copy()
        for i in range(0, len(remove_assert_Lines)):
            # get Space character prefix
            space_prefix = re.match(r'\s*', remove_assert_Lines[i]).group()
            if filt_assert == True and "//@ assert" in remove_assert_Lines[i].strip():
                # remove_assert_Lines[i] = space_prefix + "\n"
                remove_assert_Lines[i] = remove_assert_Lines[i].replace("//@ assert", "// @ assert")
        f.writelines(remove_assert_Lines)


def write_into_final_c_file(Output_folder, mfName, suffix_str, InfillLines, is_simplified = False):
    if is_simplified == True:
        outputfile = Output_folder + '/' + mfName + "_final_simplified" + suffix_str
    else:
        outputfile = Output_folder + '/' + mfName + "_final" + suffix_str
    with open(outputfile, 'w') as f:
        tmp_Lines = InfillLines.copy()
        for i in range(0, len(tmp_Lines)):
            # get Space character prefix
            if "/* @ >>> INFILL <<< */\n" in tmp_Lines[i].strip():
                tmp_Lines[i] = tmp_Lines[i].replace("/* @ >>> INFILL <<< */\n", "")
                break
        f.writelines(tmp_Lines)
    return outputfile


def set_next_api_key():
    max_api_id = int(os.environ.get('OPENAI_API_KEY_NUM'))
    cur_api_id = int(os.environ.get('CUR_OPENAI_API_KEY_ID'))  # Get the current API ID from the environment variable

    if cur_api_id == max_api_id:  # If the current API ID is equal to the maximum number of API IDs, reset the API key to the first one
        cur_api_id = 1
    else:  # Otherwise, increment the API ID
        cur_api_id = cur_api_id + 1

    # os.environ['OPENAI_API_KEY'] = decode_api_key(os.environ.get('OPENAI_API_KEY_' + str(cur_api_id-1)).encode()).decode()

    # os.environ['BALANCE'] = os.environ.get('BALANCE_' + str(cur_api_id-1))
    # os.environ['CUR_OPENAI_API_KEY_ID'] = str(cur_api_id) # Set the environment variable to record the current api_key_no


# formate time
def formateTime(seconds):
    '''
    Turn a time interval in seconds into the format of hh:mm:ss.sssss
    '''
    hours, rem = divmod(seconds, 3600)
    minutes, s = divmod(rem, 60)
    return '{:0>2}:{:0>2}:{:08.5f}'.format(int(hours), int(minutes), s)


# write to file
def write_to_file(file_name, content):
    with open(file_name, 'w') as f:
        f.write(content)

# remove one line from the file based on the given line number
def remove_one_line_from_the_file(filename, linenum):
    pop_line = ""
    # open the file in read mode and store the lines in a list
    with open(filename, "r") as f:
        lines = f.readlines()
        # check if the line number is valid
        if 0 < linenum <= len(lines):
            # remove the line at the given index
            pop_line = lines[linenum - 1].strip()
            lines.pop(linenum - 1)
            # open the file in write mode and write the modified lines
            with open(filename, "w") as f:
                for line in lines:
                    f.write(line)
        else:
            # print an error message if the line number is invalid
            print("remove_one_line_from_the_file(): Invalid line number")
    
    return pop_line


# inequality segmentation
def inequality_segmentation(input_str):
    # print("@@@@@@@@@@@@@@@@@@@@@@", input_str)
    if input_str.endswith(";"):
        input_str = input_str[:-1]
    # 初始化一个空列表
    inequality = []
    inequality_list = []
    # 用空格分割输入的字符串
    tokens = input_str.split()
    # 遍历每个token
    for i in range(0, len(tokens)):
        if tokens[i] == '<' or tokens[i] == '<=' or tokens[i] == '>' or tokens[i] == '>=':
            # 获取token的左边和右边的变量或表达式
            this_s = tokens[i]
            left = ""
            right = ""
            # from i to 0 find the first variable or expression
            for j in range(i-1, -1, -1):
                if tokens[j] == '<' or tokens[j] == '<=' or tokens[j] == '>' or tokens[j] == '>=':
                    left = ' '.join(tokens[j+1:i])
                    break
                elif j == 0:
                    left = ' '.join(tokens[j:i])
                else:
                    continue
            # from i to the end find the first variable or expression
            for j in range(i+1, len(tokens)):
                if tokens[j] == '<' or tokens[j] == '<=' or tokens[j] == '>' or tokens[j] == '>=':
                    right = ' '.join(tokens[i+1:j])
                    break
                elif j == len(tokens)-1:
                    right = ' '.join(tokens[i+1:j+1])
                else:
                    continue
            if left != "" and right != "":
                inequality_list.append([left, this_s, right])
        else:
            continue
    
    # 规范成小于号方向
    for each in inequality_list:
        if each[1] == '>':
            inequality.append(each[2] + " < " + each[0])
        elif each[1] == '>=':
            inequality.append(each[2] + " <= " + each[0])
        else:
            inequality.append(each[0] + " " + each[1] + " " + each[2])
    
    # print("@@@@@@@@@@@@@@@@@@@@@@", inequality, "\n")
    # 返回不等式列表
    return inequality