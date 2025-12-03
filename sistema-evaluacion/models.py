from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class Estudiante(db.Model):
    __tablename__ = 'estudiantes'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    correo = db.Column(db.String(100))
    carrera = db.Column(db.String(100))
    fecha_registro = db.Column(db.Date)

class Trabajo(db.Model):
    __tablename__ = 'trabajos'
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(100))
    estudiante_id = db.Column(db.Integer, db.ForeignKey('estudiantes.id'), nullable=False)

    estudiante = db.relationship('Estudiante', backref='trabajos', lazy=True)

class Criterio(db.Model):
    __tablename__ = 'criterios'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    ponderacion = db.Column(db.Float, nullable=False)
    trabajo_id = db.Column(db.Integer, db.ForeignKey('trabajos.id'), nullable=False)

    trabajo = db.relationship('Trabajo', backref='criterios', lazy=True)

class Evaluacion(db.Model):
    __tablename__ = 'evaluaciones'
    id = db.Column(db.Integer, primary_key=True)
    trabajo_id = db.Column(db.Integer, db.ForeignKey('trabajos.id'), nullable=False)
    criterio_id = db.Column(db.Integer, db.ForeignKey('criterios.id'), nullable=False)
    nota = db.Column(db.Float, nullable=False) 

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    correo = db.Column(db.String(120), unique=True, nullable=False)
    clave_hash = db.Column(db.String(300), nullable=False)

    def set_clave(self, clave):
        """Genera y guarda el hash de la contraseña"""
        self.clave_hash = generate_password_hash(clave)

    def verificar_clave(self, clave):
        """Verifica si la contraseña ingresada coincide con el hash"""
        return check_password_hash(self.clave_hash, clave)
