import math

class WaitingLinesArrival:
    def __init__(self, lambda_value:int):
        self.lambda_value = lambda_value
        self.iat = 0
        self.at = 0

    def next_arrival_interval_time(self, number:float):
        self.iat = - math.log(1 - number, math.e) / self.lambda_value
        self.at += self.iat
        return self.iat