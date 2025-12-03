from models import Trabajo

class TrabajoFactory:
    @staticmethod
    def crear_trabajo(tipo, titulo, estudiante_id):
        return Trabajo(titulo=titulo, tipo=tipo, estudiante_id=estudiante_id)
