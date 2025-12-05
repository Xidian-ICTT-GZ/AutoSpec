#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import os, sys
import datetime
from typing import List
from src.parse_args import *
from LLM4Veri.src.llmveri import *
from src.baselib import *
from LLM4Veri.src.config_manager import *


MAX_ITERATION_TIMES = 5

def main(argv: List[str]) -> None:
    # Parse the command line arguments
    gpt_file, gpt_task, pointed_output_file, llm_model, enable_mutation = parse_args(argv)
    c_files = []

    try:
        # Get the absolute path of the current file (main.py)
        current_file_path = os.path.abspath(__file__)
        
        # Move up one level (from LLM4Veri/ to /app/)
        root_dir = os.path.dirname(os.path.dirname(current_file_path)) 
        
        # Construct the target path: /app/config/models_config.yaml
        config_file_path = os.path.join(root_dir, 'config', 'models_config.yaml')
        
    except Exception as e:
        print(f"❌ Path calculation error: {e}")
        sys.exit(1)
    
    try:
        # Load the configuration using the calculated absolute path
        model_config = ConfigLoader.get_model_config(llm_model, config_file_path=config_file_path)
        # print(f"✅ [DEBUG] Successfully loaded configuration for model '{llm_model}'. Platform: {model_config.platform}")
        
    except ValueError as e:
        print(f"❌ Error: Failed to load model configuration. {e}")
        sys.exit(1)

    if os.path.isdir(gpt_file):
        for filename in os.listdir(gpt_file):
            if filename.endswith('.c'):
                file_path = os.path.join(gpt_file, filename)
                c_files.append(file_path)
    else:
        c_files.append(gpt_file)
    
    pickleFile = gpt_file+'.pickle'
    if os.path.exists(pickleFile):
                # Load the pickle
        with open(gpt_file + ".pickle", "rb") as data:
            SAVE_PICKLE = pickle.load(data)
            if SAVE_PICKLE['Status'] == 0:
                os.remove(pickleFile)
            else:
                pass

    # Start
    iteration_times = 0
    llms_query_times = datetime.timedelta(0)
    total_solve_time = datetime.timedelta(0)
    tokens_usage = 0
            
    for i in range(MAX_ITERATION_TIMES):
        try:
            outputfolder = auto_naming_output_folder(pointed_output_file, gpt_file, False)
            ret, cur_query_times, cur_solve_time, cur_tokens_usage = LLMVeri_Main(
                gpt_file, 
                gpt_task, 
                outputfolder, 
                model_config,  # Pass the ModelConfig object
                enable_mutation
            )
            iteration_times = iteration_times + 1
            llms_query_times = llms_query_times + cur_query_times
            total_solve_time = total_solve_time + cur_solve_time
            tokens_usage = tokens_usage + cur_tokens_usage
            if ret == True:
                break
        except Exception as e:
            print(e)
            raise e
            
    print("llms_query_times =", llms_query_times)
    print("total_solve_time =", total_solve_time)
    print("tokens_usage =", tokens_usage)
    print("@@@", iteration_times, "@@@")
    # End


if __name__ == "__main__":
    starttime = datetime.datetime.now()
    for i in range(0, len(sys.argv)):
        if '--enable-mutation' == sys.argv[i]:
            sys.argv[i] = '-u'
            break
    main(sys.argv[1:])
    endtime = datetime.datetime.now()
    print("\nstart time: ", starttime)
    print("end time: ", endtime)
    print("@@@ Finished @@@")