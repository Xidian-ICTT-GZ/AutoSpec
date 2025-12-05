import os
import sys
import argparse
import shutil
import subprocess
import concurrent.futures
import pickle
import re
import json
from datetime import timedelta
from collections import OrderedDict
from tqdm import tqdm
from typing import List, Dict, Any, Tuple


# Ensure the project root directory is in PATH
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT_DIR)

# Import the configuration manager
try:
    from LLM4Veri.src.config_manager import ConfigLoader, ModelConfig
except ImportError:
    print("FATAL: Unable to import ConfigLoader. Please check the path of LLM4Veri/src/config_manager.py.")
    sys.exit(1)

# Path to the configuration file
CONFIG_FILE_PATH = os.path.join(ROOT_DIR, 'config', 'models_config.yaml')
# Path to the main.py script
FUZZ_SCRIPT_PATH = os.path.join(ROOT_DIR, 'LLM4Veri', 'main.py')
# Temporary workspace
TMP_DIR = os.path.join(ROOT_DIR, 'tmp_autofuzz_workspace')

def extract_metrics_from_pickle(pickle_file_path: str) -> Dict[str, Any]:
    """
    Load and parse the pickle file to extract required metrics.
    """
    try:
        with open(pickle_file_path, "rb") as f:
            data = pickle.load(f)
            
        if not isinstance(data, dict):
            # If the content of the pickle is not a dictionary, consider it invalid
            return {"Status": "Check", "llm_time_sec": 0.0, "total_solve_time_sec": 0.0, "error": "Invalid pickle content."}

        # Extract and validate the Status
        status = data.get('Status')
        if status not in (0, 1):
            # If Status is not 0 or 1, consider it invalid
            return {"Status": "Check", "llm_time_sec": 0.0, "total_solve_time_sec": 0.0, "error": f"Invalid Status value: {status}."}
        
        # Extract time metrics (convert to seconds)
        llms_query_times = data.get('llms_query_times', timedelta(0)).total_seconds()
        total_solve_time = data.get('total_solve_time', timedelta(0)).total_seconds()
        
        # Return the original status code (0 or 1)
        return {
            "Status": status, 
            "llm_time_sec": llms_query_times,
            "total_solve_time_sec": total_solve_time,
        }

    except Exception as e:
        # Handle any other parsing errors (e.g., corrupted file, missing keys)
        return {"Status": "Check", "llm_time_sec": 0.0, "total_solve_time_sec": 0.0, "error": f"Pickle loading failure: {str(e)}"}

# ----------------------------------------------------------------------
# 1. Single model experiment executor (subprocess call)
# ----------------------------------------------------------------------

def run_single_model_experiment(model_name: str, model_config: ModelConfig, duplicated_input_dir: str, file_list: List[str], pbar: tqdm) -> List[Dict[str, Any]]:    
    """
    For a single model, iterate through all .c files in its dedicated directory and call main.py via the command line.
    """
    print(f"[{model_name}] Task started: Processing directory {duplicated_input_dir}")
    # Result dictionary, where the key is the file name and the value is the result record
    results: Dict[str, Dict[str, Any]] = {} 
    
    for filename in os.listdir(duplicated_input_dir):
        if not filename.endswith('.c'):
            continue

        file_path = os.path.join(duplicated_input_dir, filename)
        command = [ # ... (command construction remains unchanged) ...
            "python3",
            FUZZ_SCRIPT_PATH,
            "-f", file_path,
            "-m", model_name,
            "-t", "0",
            "-o", os.path.join("out", model_name, os.path.splitext(filename)[0])
        ]
        
        print(f"[{model_name}] Running {filename}...")
        pickle_file = file_path + '.pickle'

        # Ensure old pickle files are deleted before running to avoid interference
        if os.path.exists(pickle_file):
            os.remove(pickle_file)

        # Default failure status, which will always be recorded
        file_result = {
            "model_name": model_name,
            "file_name": filename,
            "Status": "Check", # Default status is Check
            "llm_time_sec": 0.0,
            "total_solve_time_sec": 0.0,
            "error": "Execution failed (Subprocess crash or Timeout)."
        }
        
        try:
            # Execute the command
            result = subprocess.run(
                command, 
                check=False, 
                capture_output=True, 
                text=True, 
                encoding='utf-8',
                timeout=300 # Set a total timeout
            )
            
            # 1. Check if the pickle file exists
            if not os.path.exists(pickle_file):
                # If not generated, keep the file_result Status as 'Check'
                pass # The error field remains the default "Execution failed..."
            else:
                # 2. Pickle file exists -> Try to extract metrics
                metrics = extract_metrics_from_pickle(pickle_file)
                
                # If metrics["Status"] is not Check, update the result
                if metrics["Status"] != "Check":
                    file_result.update({
                        "Status": metrics["Status"],
                        "llm_time_sec": metrics["llm_time_sec"],
                        "total_solve_time_sec": metrics["total_solve_time_sec"],
                    })
                    # Successfully updated, clear the default error message
                    if 'error' in file_result:
                        del file_result['error']
                else:
                    # If metrics["Status"] is Check (Pickle parsing failed or Status is invalid)
                    # Keep the file_result Status as 'Check' and inherit the parsing error message
                    if 'error' in metrics:
                        file_result['error'] = metrics['error']


        except Exception as e:
            # Catch any unexpected Python errors (e.g., os.listdir failure, etc.), keep Status as Check
            print(f"[{model_name}] ❌ {filename} Internal error occurred: {e}")
            file_result["error"] = f"Internal Python error in auto_run: {str(e)}"
        
        finally:
            # [Key] After the task is completed, update the overall progress bar
            pbar.update(1)
            # Use tqdm.write for thread-safe output
            tqdm.write(f"[{model_name}] ✅ Completed {filename} (Status: {file_result.get('Status')})")

        # No matter what happens, record the current result
        results[filename] = file_result
            
    return list(results.values())

def save_results_to_jsonl(final_results: List[Dict[str, Any]], original_input_dir: str, root_dir: str):
    """
    Save the aggregated experiment results to a JSONL file, ensuring file_name is first and grouped by model.
    """
    
    # Extract the original input folder name as an identifier for the file name (e.g., '11')
    folder_name = os.path.basename(original_input_dir.rstrip(os.sep)) # Use rstrip to ensure the trailing slash at the end of the path does not affect basename
    
    # 1. Group by model name
    results_by_model: Dict[str, List[Dict[str, Any]]] = {}
    for result in final_results:
        # Ensure each result has a model_name
        model_name = result.get('model_name', 'unknown_model')
        if model_name == 'unknown_model':
            # This should be avoided in run_single_model_experiment
            print(f"Warning: Found result without model_name: {result}")
        
        if model_name not in results_by_model:
            results_by_model[model_name] = []
        
        # 2. Reorganize and enforce key order
        # Use OrderedDict or create a new dictionary to ensure order (from Python 3.7+, the standard dictionary maintains insertion order)
        
        final_record = OrderedDict([
            ('filename', result.get('file_name', 'N/A')),
            # Map Status field, if it is 'Check', keep as string; if it is 0/1, keep as number
            ('Status', result.get('Status', 'N/A')), 
            ('llm_time_sec', result.get('llm_time_sec', 0.0)),
            ('total_solve_time_sec', result.get('total_solve_time_sec', 0.0)),
        ])
        
        # Add optional error field
        if 'error' in result:
             final_record['error'] = result['error']
             
        results_by_model[model_name].append(final_record)
        
    print("\n--- 💾 Saving final experiment results ---")
    
    # Create results directory
    results_dir = os.path.join(root_dir, 'experiment_results')
    os.makedirs(results_dir, exist_ok=True)
    
    # 3. Write to file
    for model_name, results_list in results_by_model.items():
        # Exclude unknown_model files
        if model_name == 'unknown_model':
            continue 
            
        output_filename = f"{model_name}_{folder_name}_result.jsonl"
        output_path = os.path.join(results_dir, output_filename)
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                for record in results_list:
                    # Use standard json.dumps to write in JSON Lines format
                    f.write(json.dumps(record, ensure_ascii=False) + '\n')
            print(f"✅ {model_name} results saved successfully: {output_path}")
            
        except Exception as e:
            print(f"❌ {model_name} results saving failed: {e}")

# ----------------------------------------------------------------------
# 2. auto_run.py main logic
# ----------------------------------------------------------------------

def parse_auto_run_args():
    """Parse command line arguments for auto_run.py"""
    parser = argparse.ArgumentParser(description="Multi-model concurrent reduction generation experiment coordinator.")
    parser.add_argument('-i', '--input_dir', required=True, help='Path to the original input folder containing .c files.')
    parser.add_argument('-m', '--models', required=True, nargs='+', help='List of model names to run (corresponding to ModelMap keys in models_config.yaml).')
    return parser.parse_args()


def main():
    args = parse_auto_run_args()
    original_input_dir = os.path.abspath(args.input_dir)
    model_names_to_run = args.models
    
    # 1. Stage I: Load all model configurations
    all_model_configs: Dict[str, ModelConfig] = {}
    print("--- 📚 Loading model configurations ---")
    try:
        # Load the model configurations specified by the user one by one
        for name in model_names_to_run:
            all_model_configs[name] = ConfigLoader.get_model_config(name, config_file_path=CONFIG_FILE_PATH)
        
        if not all_model_configs:
            print("❌ Error: Failed to load any model configurations, exiting.")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error: Failed to load model configurations. {e}")
        sys.exit(1)

    # 2. Stage II: Space isolation (folder copying)
    copied_dirs: Dict[str, str] = {}
    if os.path.exists(TMP_DIR):
        shutil.rmtree(TMP_DIR) # Clean up old temporary directory
    os.makedirs(TMP_DIR)
    
    print("\n--- 📂 Creating dedicated workspace directories ---")
    try:
        for model_name in all_model_configs.keys():
            # Construct the model-specific directory name: /app/tmp_autofuzz_workspace/qwen-turbo_benchmarks
            base_dir_name = os.path.basename(original_input_dir)
            target_dir_name = f"{model_name}_{base_dir_name}"
            target_path = os.path.join(TMP_DIR, target_dir_name)
            
            # Use shutil.copytree to fully copy the folder
            shutil.copytree(original_input_dir, target_path)
            copied_dirs[model_name] = target_path
            print(f"✅ Created directory: {target_path}")
            
    except Exception as e:
        print(f"❌ Error: Folder copying failed. Please check if the original path {original_input_dir} exists. {e}")
        shutil.rmtree(TMP_DIR)
        sys.exit(1)

    # 2.5 Get the list of all files and the total number of tasks
    # Assume the file list in the input directory is fetched only once
    file_list_original = [f for f in os.listdir(original_input_dir) if f.endswith('.c')]

    MAX_WORKERS = len(all_model_configs) # Determine the number of worker processes based on the number of loaded models
    TOTAL_FILES = len(file_list_original)
    TOTAL_TASKS = TOTAL_FILES * MAX_WORKERS # Total number of tasks = number of files * number of models
    
    # 3. Stage III: Concurrent scheduling
    results_futures: List[concurrent.futures.Future] = []
    MAX_WORKERS = len(copied_dirs)
    
    print(f"\n--- 🚀 Starting {MAX_WORKERS} concurrent tasks (Total {TOTAL_TASKS} file executions) ---")
    
    # [New] Initialize progress bar
    pbar = tqdm(total=TOTAL_TASKS, desc="Overall Progress", unit="file", bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]")

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            for model_name, duplicated_dir in copied_dirs.items():
                model_config = all_model_configs[model_name]
                
                # [Key] Submit concurrent tasks, passing in file_list and progress bar object pbar
                future = executor.submit(run_single_model_experiment, 
                                         model_name, 
                                         model_config, 
                                         duplicated_dir, 
                                         file_list_original, # Pass in the file list
                                         pbar)                # Pass in the progress bar
                results_futures.append(future)
            
            # 4. Stage V: Wait for results and aggregate
            final_results: List[Dict[str, Any]] = []
            
            # Note: Here we no longer use as_completed to block the main thread, but let the progress bar update in the background
            # We just need to wait for all future results
            for future in results_futures:
                results_list = future.result() 
                final_results.extend(results_list)
            
            # Save final results to JSONL file
            ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # Reconfirm the root directory
            save_results_to_jsonl(final_results, original_input_dir, ROOT_DIR)

    except Exception as e:
        print(f"❌ Experiment run exception: {e}")
        # Ensure the progress bar is closed on abnormal exit
        pbar.close()
        raise e
        
    finally:
        # Ensure the progress bar is closed before exiting
        pbar.close()
        print(f"\n--- 🧹 Cleaning up temporary work directory {TMP_DIR} ---")
        shutil.rmtree(TMP_DIR)



if __name__ == "__main__":
    # Ensure that when running auto_run.py, the project path is correctly set, allowing module imports
    # ... (this should be handled in the startup script, but keep the main structure)
    main()