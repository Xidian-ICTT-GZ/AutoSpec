import os
import glob
import subprocess
import re
import shutil
import json
import argparse

# Timeout for Frama-C (seconds) to prevent certain files from hanging
TIMEOUT_SECONDS = 60

def run_framac_and_check(file_path):
    """
    Call frama-c to verify the file and check the output to determine success.
    Returns: (is_success (bool), output_log (str))
    """
    # Construct the command: frama-c -wp path/*.c
    cmd = ["frama-c", "-wp", file_path]
    
    try:
        # Execute the command, capturing stdout and stderr
        # The timeout parameter prevents long hangs
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=TIMEOUT_SECONDS
        )
        output = result.stdout
        
        # If stdout is empty, sometimes error messages are in stderr, so concatenate for debugging
        # But usually, WP proof results are in stdout
        full_log = output + "\n" + result.stderr

        # Regex match: [wp] Proved goals:    n / m
        # \s+ matches one or more spaces
        # (\d+) captures numbers
        match = re.search(r'\[wp\] Proved goals:\s+(\d+)\s+/\s+(\d+)', output)
        
        if match:
            proved_n = int(match.group(1))
            total_m = int(match.group(2))
            
            # Core judgment logic: n == m means success
            # Note: If m=0 (no goals), it is usually considered as nothing to do. This depends on specific needs,
            # but usually, a valid program has at least one goal. If n=m=0, treat as success.
            if proved_n == total_m:
                return True, full_log
            else:
                return False, full_log
        else:
            # If this line is not found, it means Frama-C might have errored or generated no proof goals
            return False, full_log

    except subprocess.TimeoutExpired:
        print(f"  [Timeout] File verification timed out ({TIMEOUT_SECONDS}s): {file_path}")
        return False, "Timeout"
    except Exception as e:
        print(f"  [Exception] Execution error: {e}")
        return False, str(e)

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Run Frama-C verification on .c files.")
    parser.add_argument("-i", "--input", required=True, help="Path to the input directory containing .c files.")
    parser.add_argument("-o", "--output", required=True, help="Path to the output directory for verified files.")
    args = parser.parse_args()

    input_dir = args.input
    output_dir = args.output
    log_file = os.path.join(output_dir, "verification_results.jsonl")

    # 1. Prepare the output directory
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")

    # 2. Get all .c files
    # Assume the input_dir contains all the .c files to be verified
    search_pattern = os.path.join(input_dir, "*.c")
    files = glob.glob(search_pattern)
    
    if not files:
        print(f"No .c files found in {input_dir}.")
        return

    print(f"Starting verification, found {len(files)} files...")
    
    results = []
    success_count = 0

    # 3. Process each file
    for file_path in files:
        file_name = os.path.basename(file_path)
        print(f"Verifying: {file_name} ...", end="", flush=True)
        
        is_success, _ = run_framac_and_check(file_path)
        
        # Record status: 1 for success, 0 for failure
        status_code = 1 if is_success else 0
        
        if is_success:
            print(" [Success]")
            success_count += 1
            
            # 4. If successful, rename and save as
            # Original: 123.c -> Target: 123_verified.c
            name_part, ext_part = os.path.splitext(file_name)
            new_name = f"{name_part}_verified{ext_part}"
            target_path = os.path.join(output_dir, new_name)
            
            try:
                shutil.copy2(file_path, target_path)
            except IOError as e:
                print(f"  [Error] Failed to copy file: {e}")
        else:
            print(" [Failed]")

        # Add to results list
        results.append({
            "file_name": file_name,
            "status": status_code
        })

    # 5. Write to JSONL log
    try:
        with open(log_file, 'w', encoding='utf-8') as f:
            for entry in results:
                f.write(json.dumps(entry) + '\n')
        print(f"\nVerification complete.")
        print(f"Number of successful files: {success_count} / {len(files)}")
        print(f"Successful files saved to: {output_dir}")
        print(f"Result log saved to: {log_file}")
    except IOError as e:
        print(f"Failed to write log file: {e}")

if __name__ == "__main__":
    main()