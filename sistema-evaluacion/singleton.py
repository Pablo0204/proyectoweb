class ConfiguracionGlobal:
    _instancia = None

    def __new__(cls):
        if cls._instancia is None:
            cls._instancia = super(ConfiguracionGlobal, cls).__new__(cls)
            cls._instancia.institucion = "Universidad Adventista de Chile"
            cls._instancia.escala_notas = "0-100"
            cls._instancia.formato_acta = "texto"
        return cls._instancia

    def set_institucion(self, nombre):
        self.institucion = nombre

    def set_formato_acta(self, formato):
        self.formato_acta = formato
