import os
from openai import OpenAI, OpenAIError

# --- 1. Initialize OpenAI Client ---

# Get API key from environment variables
# You must set this variable in your terminal first:
# export OPENAI_API_KEY='sk-...'
api_key = os.environ.get("OPENAI_API_KEY")
base_url = "https://api.openai-proxy.org/v1"
if not api_key:
    print("Error: OPENAI_API_KEY environment variable is not set.")

client = OpenAI(api_key=api_key, base_url=base_url)

# --- 2. Define the System Prompt ---

SYSTEM_PROMPT = """
You are an expert assistant specializing in generating ACSL specifications for the Frama-C framework.
Your task is to generate a single 'loop variant' clause based on the provided context (loop annotations, loop condition, and loop body).

Your response MUST adhere to the following strict rules:
1.  You MUST return ONLY the single-line 'loop variant' clause.
2.  Do NOT include any explanations, preambles, or Markdown formatting (like ```c ... ```).
3.  The 'loop variant' must satisfy ACSL requirements: it must be a non-negative integer expression that strictly decreases on each loop iteration.
4.  If the context is a 'for' loop like 'for (i = 0; i < n; i++)', a good variant is 'n - i'.
5.  If the context is a 'while' loop like 'while (j < n)' with 'j++' in the body, a good variant is 'n - j'.
6.  If the context is a decrementing 'while' loop like 'while (i > 0)' with 'i--' in the body, a good variant is 'i'.

Example of a valid response:
loop variant n - j;
"""

# --- 3. Completed LLM Function ---

def generate_loop_variant_llm(context_prompt: str) -> str:
    """
    Uses the OpenAI API (e.g., GPT-3.5 Turbo) to generate
    a 'loop variant' clause based on the provided context.
    
    Args:
        context_prompt: The full prompt containing the task description
                        and the code context (annotations, condition, body).
    
    Returns:
        A string containing the single-line 'loop variant' clause,
        or an error comment if the API call fails.
    """
    if not api_key:
        print("--- [LLM error] OPENAI_API_KEY not set. Skipping API call. ---")
        return "/*@ LLM_SKIPPED_NO_API_KEY; */"
        
    try:
        completion = client.chat.completions.create(
            # We recommend gpt-3.5-turbo for speed and cost.
            # For more complex loops, you can swap to "gpt-4" or "gpt-4-turbo".
            model="gpt-3.5-turbo",
            
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": context_prompt  # The full prompt assembled by your script
                }
            ],
            
            # Use a low temperature for more predictable,
            # deterministic results in code generation tasks.
            temperature=0.1,
            max_tokens=100, # A loop variant is usually short
            n=1            # We only need one generation
        )
        
        # Extract the response text
        response_text = completion.choices[0].message.content
        
        if response_text:
            # Clean up potential leading/trailing whitespace
            clean_response = response_text.strip()
            
            # Basic validation that it looks like what we want
            if clean_response.startswith("loop variant"):
                print(f"--- [LLM Success] Received: {clean_response} ---")
                return clean_response
            else:
                print(f"--- [LLM Warning] Received non-conformant response: {clean_response} ---")
                # Return it anyway for debugging
                return clean_response
        else:
            return "/*@ LLM_RETURNED_EMPTY; */"

    except OpenAIError as e:
        print(f"--- [LLM Error] OpenAI API call failed: {e} ---")
        return f"/*@ LLM_API_ERROR: {e} */"
    except Exception as e:
        print(f"--- [LLM Error] An unexpected error occurred: {e} ---")
        return f"/*@ LLM_UNKNOWN_ERROR: {e} */"

# --- 4. Example Call (for Testing) ---

if __name__ == "__main__":
    if not api_key:
        print("Cannot run test because OPENAI_API_KEY is not set.")
    else:
        # This simulates the prompt that your generator script would assemble
        test_prompt = """
[TASK]
Please generate a 'loop variant' clause for the following C language loop.
The 'loop variant' must satisfy ACSL requirements: it must be a non-negative integer expression that strictly decreases on each loop iteration.
Please return ONLY the single-line 'loop variant' clause, e.g.: loop variant n - i;

======= START CONTEXT =======

[Existing Loop Annotations]
/*@
loop invariant x + y == k;
loop invariant m < n;
loop invariant j <= n;
loop invariant 0 <= m;
loop invariant 0 <= j;
loop assigns y;
loop assigns x;
loop assigns m;
loop assigns j;
*/

[Loop Condition]
while (j < n)

[Loop Body]
{
  if (j == i) {
    x++;
    y--;
  } else {
    y++;
    x--;
  }
  if (unknown1())
    m = j;
  j++;
}

======= END CONTEXT =======

[TASK REPEAT]
Return ONLY the single-line 'loop variant' clause.
"""
        
        print("--- Calling OpenAI API... ---")
        variant = generate_loop_variant_llm(test_prompt)
        print("\n--- API Call Complete ---")
        print(f"Final returned string: {variant}")