from langchain_core.tools import tool

@tool
def calculator(expression: str) -> str:
    """Evaluate a mathematical expression.
    
    Args:
        expression: A math expression like "2 + 2" or "10 * 5"
    
    Examples:
        - "2 + 2" -> "4"
        - "10 * 5" -> "50"
        - "100 / 4" -> "25.0"
    """
    try:
        # Security: Use limited eval with no builtins
        # Only allow basic math operations
        allowed_names = {
            'abs': abs, 'round': round, 'min': min, 'max': max,
            'sum': sum, 'pow': pow
        }
        result = eval(expression, {"__builtins__": {}}, allowed_names)
        return str(result)
    except Exception as e:
        return f"Error: {str(e)}"
