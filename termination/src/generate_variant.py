import re
import os
import sys
import glob
import argparse

from llmcore import generate_loop_variant_llm

# --- 2. Core Processing Logic ---

def find_matching_brace(code_snippet: str, start_index: int) -> int:
    """
    Starting from start_index, find the matching '}'.
    This is critical for extracting the loop body.
    """
    try:
        open_brace_index = code_snippet.index('{', start_index)
    except ValueError:
        return -1 # No '{'

    brace_level = 1
    current_index = open_brace_index + 1
    
    while current_index < len(code_snippet):
        char = code_snippet[current_index]
        if char == '{':
            brace_level += 1
        elif char == '}':
            brace_level -= 1
            if brace_level == 0:
                # Found matching '}'
                return current_index + 1
        current_index += 1
    
    return -1 # No matching '}' found

def inject_variant(annotation_block: str, variant_string: str) -> str:
    """
    Inject the variant string at the end of the annotation block (before */).
    Strictly adhere to Frama-C's positional requirements.
    """
    # Find the last '*/'
    end_marker_pos = annotation_block.rfind('*/')
    if end_marker_pos == -1:
        return annotation_block # Malformed block

    content_before_end = annotation_block[:end_marker_pos].rstrip()
    
    # Infer correct indentation
    last_line_break = content_before_end.rfind('\n')
    indent_line = content_before_end[last_line_break + 1:]
    indent = " " * (len(indent_line) - len(indent_line.lstrip()))
    
    # Assemble the new annotation block
    new_variant_line = f"{indent}{variant_string}"
    return f"{content_before_end}\n{new_variant_line}\n{indent}*/"

def process_single_file(input_filepath: str, output_filepath: str):
    """
    Read the file, find all loops, generate and inject loop variants for loops missing variants.
    """
    try:
        with open(input_filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: File not found {input_filepath}")
        return
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    # Regular expression search:
    # (Group 1: Complete ACSL annotation block)
    # (Group 2: 'while' or 'for' statement)
    # We use [\s\S]*? to match everything including newlines
    loop_pattern = re.compile(
        r'(\/\*@[\s\S]*?\*\/\s*)((?:while|for)\s*\(.*\))',
        re.MULTILINE
    )
    
    # Find all matches
    matches = list(loop_pattern.finditer(content))
    
    # Replace from back to front to prevent index shifting
    for match in reversed(matches):
        annotation_block = match.group(1)
        while_line = match.group(2).strip()
        
        # Check if variant already exists
        if "loop variant" in annotation_block:
            print(f"Variant already exists, skipping: {while_line}")
            continue
            
        print(f"Detected loop missing variant: {while_line}")

        # 1. Locate and extract loop body
        loop_body_start_index = match.end(2)
        loop_body_end_index = find_matching_brace(content, loop_body_start_index)
        
        if loop_body_end_index == -1:
            print(f"  [Warning] Could not find loop body '{{ ... }}' for {while_line}. Skipping.")
            continue
            
        loop_body = content[loop_body_start_index:loop_body_end_index].strip()
        
        # 2. Assemble the prompt
        prompt_context = f"""
======= Start Context =======
[Existing Loop Annotation]
{annotation_block}

[Loop Condition]
{while_line}

[Loop Body]
{loop_body}
======= End Context =======

[Task]
Please generate a 'loop variant' clause for the above C language while loop.
The 'loop variant' must meet ACSL requirements: it is a non-negative integer expression and strictly decreases after each loop iteration.
Please return only a single-line 'loop variant' clause, e.g., loop variant n - j;
"""
        
        # 3. Call (simulated) LLM
        new_variant_string = generate_loop_variant_llm(prompt_context)
        
        # 4. Inject variant
        modified_annotation_block = inject_variant(annotation_block, new_variant_string)
        
        # 5. Replace the old annotation block in the original content
        # We only replace the annotation block (match.span(1))
        start_index, end_index = match.span(1)
        content = content[:start_index] + modified_annotation_block + content[end_index:]

    # 6. Write to new file
    try:
        with open(output_filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"\nProcessing complete. Results written to: {output_filepath}")
    except Exception as e:
        print(f"Error writing file: {e}")

# --- 3. batch process ---
def batch_process(input_dir: str, output_dir: str):
    """Traverse the directory and process all .c files. If the file ends with _verified.c, rename it; otherwise, keep the original name."""
    
    # 1. Ensure the output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")

    # 2. Find all .c files
    search_pattern = os.path.join(input_dir, "*.c")
    files = glob.glob(search_pattern)
    
    if not files:
        print(f"No .c files found in {input_dir}.")
        return

    print(f"Found {len(files)} files to process...")

    for file_path in files:
        filename = os.path.basename(file_path)
        
        # 3. Parse and transform the filename
        # If the file is 123_verified.c -> 123.c
        # If the file is other.c -> other.c
        if filename.endswith("_verified.c"):
            new_filename = filename.replace("_verified.c", ".c")
        else:
            new_filename = filename
            
        output_path = os.path.join(output_dir, new_filename)
        
        # 4. Process a single file
        process_single_file(file_path, output_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch process .c files to generate loop variants.")
    parser.add_argument("-i", "--input", required=True, help="Path to the input directory containing .c files.")
    parser.add_argument("-o", "--output", required=True, help="Path to the output directory for processed files.")
    args = parser.parse_args()

    batch_process(args.input, args.output)