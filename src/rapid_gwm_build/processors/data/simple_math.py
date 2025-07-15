from ...registries import register_processor

@register_processor("simple_math")
def simple_math(data, expression, variables, **kwargs):
    func = string_to_function(expression, variables)

    return func(data, **kwargs)


def string_to_function(expression, variables):
    """
    Convert a string expression to a callable function.
    
    Args:
        expression (str): Mathematical expression like "x**2 + y"
        variables (list): List of variable names like ['x', 'y']
    
    Returns:
        function: Callable function
    """
    # Create parameter string for lambda
    params = ', '.join(variables)
    lambda_string = f"lambda {params}: {expression}"
    
    # Convert to function using eval
    return eval(lambda_string)