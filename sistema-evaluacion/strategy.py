from abc import ABC, abstractmethod

class CalculoNotaStrategy(ABC):
    @abstractmethod
    def calcular_aporte(self, nota, ponderacion):
        pass

class CalculoLineal(CalculoNotaStrategy):
    def calcular_aporte(self, nota, ponderacion):
        return nota * ponderacion / 100.0

class CalculoNormalizado(CalculoNotaStrategy):
    def calcular_aporte(self, nota, ponderacion):
        return (nota / 100.0) * ponderacion
