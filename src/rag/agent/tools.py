import os
import sys
import io
from tavily import TavilyClient
from langchain_core.tools import tool

@tool
def external_web_search(query: str) -> str:
    """Scrapes the public internet for software engineering documentation, code bugs, 
    up-to-date facts, definitions, or broad reference definitions when local university material 
    is insufficient or missing.
    """
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        return "External lookup failure: Tavily API token key missing from environment variables."
        
    try:
        client = TavilyClient(api_key)
        response = client.search(
            query = query, search_depth = "advanced", max_results = 3
        )
        
        results = response.json().get("results", [])
        formatted = [f"[Web Link: {r['url']}]\n{r['content']}" for r in results]
        return "\n\n---\n\n".join(formatted)
    except Exception as e:
        return f"External lookup connection network error: {str(e)}"

@tool
def calculator(expression: str) -> str:
    """Performs exact basic mathematical and arithmetic calculations (addition, subtraction, 
    multiplication, division, exponents, square roots). Pass raw equations like '144 * 12' or 'math.sqrt(255)' 
    without arbitrary conversational markup or leading text.
    """
    import math
    try:
        # Sandboxed evaluation scope limiting global code injections
        allowed_names = {k: v for k, v in math.__dict__.items() if not k.startswith("__")}
        result = eval(expression, {"__builtins__": None}, allowed_names)
        return f"Calculation Result: {result}"
    except Exception as e:
        return f"Math Evaluation Subsystem Error: {str(e)}"

@tool
def run_python(code: str) -> str:
    """Executes arbitrary Python code locally to perform advanced data analysis, statistical operations,
    mathematical matrix calculations, structural data plotting calculations, or simulations. 
    Always utilize 'print()' statements to output the final tables, arrays, values, or text-based results 
    so they can be captured by the agent console interface.
    """
    # Capture stdout streaming buffers over the execution lifespan
    old_stdout = sys.stdout
    redirected_output = io.StringIO()
    sys.stdout = redirected_output
    
    local_scope = {}
    try:
        # WARNING: In absolute untrusted production contexts, isolate this via sandboxed Docker micro-containers
        exec(code, {"__builtins__": __builtins__}, local_scope)
        sys.stdout = old_stdout
        output = redirected_output.getvalue()
        
        if not output:
            output = "Script executed successfully with no active stdout output streams. Created local entities: " + str(list(local_scope.keys()))
        return output
    except Exception as e:
        sys.stdout = old_stdout
        return f"Runtime Python Execution Crash: {str(e)}"