
def montecarlo(options: list[tuple[str, float]], random_value: float) -> str:
    """
    Realiza una simulación de Monte Carlo.
    
    :param options: Lista de tuplas (valor, probabilidad)
    :param random_value: Número pseudoaleatorio entre 0 y 1
    :return: Valor seleccionado según las probabilidades acumuladas
    """
    cumulative = 0.0
    for value, probability in options:
        cumulative += probability
        if random_value < cumulative:
            return value
    # Por si hay un pequeño error de redondeo
    return options[-1][0]