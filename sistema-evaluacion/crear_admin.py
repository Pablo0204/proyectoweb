from app import app, db
from models import Usuario

def crear_admin():
    with app.app_context():  
        admin = Usuario(
            nombre='Administrador',
            correo='pabloapala@alu.unach.cl'
        )
        admin.set_clave('pablo123')  
        db.session.add(admin)
        db.session.commit()
        print("✅ Usuario administrador creado correctamente")

if __name__ == "__main__":
    crear_admin()
