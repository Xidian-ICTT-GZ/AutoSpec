import sys
from .prompt_all import *
from .prompt_loopinv_gen import *
from .prompt_loopinv_infill import *
from .prompt_contract_gen import *
from .prompt_contract_infill import *


def get_incontext_learning_contents(content_type, sys_prompt, rag_shot, shot_num=3):
    ret_list = []
    # rag_prompt = rag_sys_prompt + "\n" + rag_shot
    rag_prompt = ''
    # print("--------------------RAG---------------------")
    # print(rag_prompt)
    if content_type == "loop_inv_gen":
        ret_list = [
            {'role': 'system', 'content': verification_gen_loop_inv},
            {'role': 'system', 'content': rag_prompt},
            {'role': 'user', 'content': gen_loop_example_1_question},
            {'role': 'assistant', 'content': gen_loop_example_1_answer},
            {'role': 'user', 'content': gen_loop_example_2_question},
            {'role': 'assistant', 'content': gen_loop_example_2_answer},
            {'role': 'user', 'content': gen_loop_example_3_question},
            {'role': 'assistant', 'content': gen_loop_example_3_answer},
            {'role': 'user', 'content': gen_loop_example_4_question},
            {'role': 'assistant', 'content': gen_loop_example_4_answer},
            {'role': 'user', 'content': gen_loop_example_5_question},
            {'role': 'assistant', 'content': gen_loop_example_5_answer},
            {'role': 'user', 'content': gen_loop_example_6_question},
            {'role': 'assistant', 'content': gen_loop_example_6_answer}
        ]
    elif content_type == 'contract_gen':
        ret_list = [
            {'role': 'system', 'content': verification_gen_contract},
            {'role': 'system', 'content': rag_prompt},
            {'role': 'user', 'content': gen_contract_example_1_question},
            {'role': 'assistant', 'content': gen_contract_example_1_answer},
            {'role': 'user', 'content': gen_contract_example_2_question},
            {'role': 'assistant', 'content': gen_contract_example_2_answer},
            {'role': 'user', 'content': gen_contract_example_3_question},
            {'role': 'assistant', 'content': gen_contract_example_3_answer},
            {'role': 'user', 'content': gen_contract_example_4_question},
            {'role': 'assistant', 'content': gen_contract_example_4_answer},
            {'role': 'user', 'content': gen_contract_example_5_question},
            {'role': 'assistant', 'content': gen_contract_example_5_answer},
            {'role': 'user', 'content': gen_contract_example_6_question},
            {'role': 'assistant', 'content': gen_contract_example_6_answer}
            ]
    elif content_type == 'loop_inv_infill':
        ret_list = [
            {'role': 'system', 'content': verification_infill_loop_inv},
            {'role': 'user', 'content': infill_loop_example_1_question},
            {'role': 'assistant', 'content': infill_loop_example_1_answer},
            {'role': 'user', 'content': infill_loop_example_2_question},
            {'role': 'assistant', 'content': infill_loop_example_2_answer},
            {'role': 'user', 'content': infill_loop_example_3_question},
            {'role': 'assistant', 'content': infill_loop_example_3_answer},
            {'role': 'user', 'content': infill_loop_example_4_question},
            {'role': 'assistant', 'content': infill_loop_example_4_answer},
            {'role': 'user', 'content': infill_loop_example_5_question},
            {'role': 'assistant', 'content': infill_loop_example_5_answer},
            {'role': 'user', 'content': infill_loop_example_6_question},
            {'role': 'assistant', 'content': infill_loop_example_6_answer}]
    elif content_type == 'contract_infill':
        ret_list = [
            {'role': 'system', 'content': sys_prompt},
            {'role': 'user', 'content': infill_contract_example_1_question},
            {'role': 'assistant', 'content': infill_contract_example_1_answer},
            {'role': 'user', 'content': infill_contract_example_2_question},
            {'role': 'assistant', 'content': infill_contract_example_2_answer},
            {'role': 'user', 'content': infill_contract_example_3_question},
            {'role': 'assistant', 'content': infill_contract_example_3_answer},
            {'role': 'user', 'content': infill_contract_example_4_question},
            {'role': 'assistant', 'content': infill_contract_example_4_answer},
            {'role': 'user', 'content': gen_contract_example_5_question},
            {'role': 'assistant', 'content': gen_contract_example_5_answer},
            {'role': 'user', 'content': gen_contract_example_6_question},
            {'role': 'assistant', 'content': gen_contract_example_6_answer}
            ]
    elif content_type == 'normal':
        # set system prompt
        if shot_num == 0:
            ret_list = [{'role': 'system', 'content': sys_prompt}]
        elif shot_num == 1:
            ret_list = [{'role': 'system', 'content': sys_prompt},
                        {'role': 'system', 'content': rag_prompt},
                        {'role': 'user', 'content': first_shot_example_question},
                        {'role': 'assistant', 'content': first_shot_example_answer}]
        elif shot_num == 2:
            ret_list = [{'role': 'system', 'content': sys_prompt},
                        {'role': 'system', 'content': rag_prompt},
                        {'role': 'user', 'content': first_shot_example_question},
                        {'role': 'assistant', 'content': first_shot_example_answer},
                        {'role': 'user', 'content': second_shot_example_question},
                        {'role': 'assistant', 'content': second_shot_example_answer}]
        elif shot_num == 3:
            ret_list = [{'role': 'system', 'content': sys_prompt},
                        {'role': 'system', 'content': rag_prompt},
                        {'role': 'user', 'content': first_shot_example_question},
                        {'role': 'assistant', 'content': first_shot_example_answer},
                        {'role': 'user', 'content': second_shot_example_question},
                        {'role': 'assistant', 'content': second_shot_example_answer},
                        {'role': 'user', 'content': third_shot_example_question},
                        {'role': 'assistant', 'content': third_shot_example_answer}]
        else:
            raise Exception("Error: shot_num is not correct: " + str(shot_num))

    elif content_type == 'loop':
        ret_list = [
            {'role': 'system', 'content': sys_prompt},
            {'role': 'system', 'content': rag_prompt},
            {'role': 'user', 'content': third_shot_example_question},
            {'role': 'assistant', 'content': third_shot_example_answer},
            {'role': 'user', 'content': loop_example_1_question},
            {'role': 'assistant', 'content': loop_example_1_answer},
            {'role': 'user', 'content': loop_example_2_question},
            {'role': 'assistant', 'content': loop_example_2_answer}]
    else:
        pass
    
    return ret_list
    