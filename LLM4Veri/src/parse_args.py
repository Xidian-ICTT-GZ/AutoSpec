import os, sys
import getopt
import argparse
from typing import List
from .baselib import *

current_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(os.path.dirname(current_path)))
from utils.qwencore import *

def parse_args(argv: List[str]) -> argparse.Namespace:
    # Parse the command line arguments using the getopt module
    try:
        opts, args = getopt.getopt(argv, "hvf:t:o:a:m:u", ["help", "version", "File=", "Task=", "Output=", "API_KEY=", "MODEL=", "enable_mutation"])

    except getopt.GetoptError:
        print('Error: main.py -f <File> -t <task> -o <outputfolder>')
        sys.exit(2)


    gpt_file = ""
    gpt_task = 0
    output_folder = ""
    llm_model = ""
    enable_mutation = False

    # Process the options list into elements of a list
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print('Syntax:')
            print('\tmain.py -f <File> -t <task> -o <outputfolder> -m <model>', "\n")
            print('Options:')
            print('\t-m <model>\t', end='')
            print('\n\t-t <task>', end='')
            print('\t 0 --> Auto')
            print('\t\t\t 3 --> Infill loop')
            print('\t\t\t 4 --> Infill contract')
            sys.exit()
            
        elif opt in ("-v", "--version"):
            print('version 1.0.0')
            sys.exit()

        elif opt in ("-f", "--file"):
            gpt_file = arg

        elif opt in ("-t", "--task"):
            if arg.isdigit():
                gpt_task = int(arg)
            else:
                gpt_task = arg

        elif opt in ("-o", "--output"):
            output_folder = arg

        elif opt in ("-m", "--model"):
            llm_model = arg
        
        elif opt in ("-u", "--enable-mutation"):
            enable_mutation = True

        elif opt in ("-a", "--api-key"):
            print(f"警告：参数 -a/--api-key '{arg}' 已被忽略。LLM API Key 现在通过环境变量（如 OPENAI_API_KEY）加载，并在 models_config.yaml 中配置。")

    if gpt_file == "" and gpt_task == "":
        print('Error: file is not specified, or the string is not specified')
        print('Tips: Using -h to view help')
        sys.exit(2)
    
    if output_folder == "":
        print("[DEBUG] output folder is not specified, use default 'out' folder")
        output_folder = auto_naming_output_folder("",gpt_file)
    else:
        output_folder = auto_naming_output_folder(output_folder, gpt_file)                                                          

    print('[DEBUG] gpt_file = ', gpt_file, ', gpt_task = ', gpt_task)
    print('[DEBUG] enable_mutation = ', enable_mutation)
    print('[DEBUG] output_folder = ', output_folder)
    print('')

    # Print the arguments list, which contains all arguments that don't start with '-' or '--'
    for i in range(0, len(args)):
        print('Argument %s is: %s' % (i + 1, args[i]))
    
    return gpt_file, gpt_task, output_folder, llm_model, enable_mutation