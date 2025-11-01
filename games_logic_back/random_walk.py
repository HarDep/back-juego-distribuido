
def random_choice(states, probabilities=None, rand_num=None):
    """
    Selects a value from 'states' using optional 'probabilities'.
    If no probabilities are provided, assumes uniform distribution.

    :param states: List of values to choose from.
    :param probabilities: Optional list of probabilities (must sum to 1).
    :param rand_num: Optional float (0-1) for deterministic testing.
    :return: One selected value from 'states'.
    """
    if not states:
        raise ValueError("States list cannot be empty.")
    
    if probabilities:
        if len(states) != len(probabilities):
            raise ValueError("States and probabilities must have the same length.")
        if not abs(sum(probabilities) - 1.0) < 1e-8:
            raise ValueError("Probabilities must sum to 1.")
    else:
        probabilities = [1 / len(states)] * len(states)

    cumulative = 0.0
    rand_value = rand_num 

    for state, prob in zip(states, probabilities):
        cumulative += prob
        if rand_value <= cumulative:
            return state

    # Fallback for numerical precision
    return states[-1]