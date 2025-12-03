from flask import Flask, request, jsonify, render_template, Response, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

from strategy import CalculoLineal
from factory import TrabajoFactory
from template_method import ActaPDF
from singleton import ConfiguracionGlobal

from models import db, Estudiante, Trabajo, Criterio, Evaluacion, Usuario

app = Flask(__name__, static_folder='static')
app.secret_key = 'pablo123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:pablo1234@localhost/sistema_evaluacion'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

@app.context_processor
def inject_year():
    return {'current_year': datetime.now().year}

@app.route('/')
def inicio():
    return render_template('dashboard.html', usuario={'nombre': 'Usuario'})

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html', usuario={'nombre': 'Usuario'})

@app.route('/panel/estudiantes')
def panel_estudiantes():
    estudiantes = Estudiante.query.all()
    return render_template('panel_estudiantes.html', estudiantes=estudiantes)

@app.route('/agregar_estudiante_web')
def agregar_estudiante_web():
    return render_template('agregar_estudiante_web.html')

@app.route('/agregar_estudiante', methods=['POST'])
def agregar_estudiante():
    data = request.get_json()
    nuevo = Estudiante(nombre=data['nombre'], correo=data.get('correo'))
    db.session.add(nuevo)
    db.session.commit()
    return jsonify({'mensaje': 'Estudiante agregado correctamente'})

@app.route('/eliminar_estudiante/<int:estudiante_id>')
def eliminar_estudiante(estudiante_id):

    try:
        estudiante = Estudiante.query.get_or_404(estudiante_id)

        trabajos = Trabajo.query.filter_by(estudiante_id=estudiante_id).all()

        for trabajo in trabajos:
            Evaluacion.query.filter_by(trabajo_id=trabajo.id).delete()
            Criterio.query.filter_by(trabajo_id=trabajo.id).delete()
            db.session.delete(trabajo)

        db.session.delete(estudiante)
        db.session.commit()

        return redirect('/panel/estudiantes')
    except Exception as e:
        db.session.rollback()
        return f"Error al eliminar el estudiante: {str(e)}", 500

@app.route('/panel/trabajos')
def panel_trabajos():
    trabajos = Trabajo.query.all()
    return render_template('panel_trabajos.html', trabajos=trabajos, Estudiante=Estudiante)

@app.route('/panel/trabajos/<int:trabajo_id>')
def panel_trabajo_detalle(trabajo_id):
    trabajo = Trabajo.query.get_or_404(trabajo_id)
    estudiante = Estudiante.query.get(trabajo.estudiante_id)
    evaluaciones = Evaluacion.query.filter_by(trabajo_id=trabajo_id).all()
    criterios = Criterio.query.filter_by(trabajo_id=trabajo_id).all()

    total = 0
    peso = 0
    for ev in evaluaciones:
        crit = next((c for c in criterios if c.id == ev.criterio_id), None)
        if crit:
            total += ev.nota * crit.ponderacion / 100
            peso += crit.ponderacion
    nota_final = round(total, 2) if peso > 0 else 'N/A'

    return render_template('panel_trabajo_detalle.html',
                           trabajo=trabajo,
                           estudiante=estudiante,
                           evaluaciones=evaluaciones,
                           criterios=criterios,
                           nota_final=nota_final)

@app.route('/agregar_trabajo_web')
def agregar_trabajo_web():
    estudiantes = Estudiante.query.all()
    return render_template('agregar_trabajo_web.html', estudiantes=estudiantes)

@app.route('/panel/criterios')
def panel_criterios():
    criterios = Criterio.query.all()
    return render_template('panel_criterios.html', criterios=criterios, Criterio=Criterio)

@app.route('/agregar_trabajo', methods=['POST'])
def agregar_trabajo():
    data = request.get_json()
    try:
        if 'criterios' not in data or not data['criterios']:
            return jsonify({'error': 'Debes definir al menos un criterio de evaluación'}), 400

        total_ponderacion = sum(c['ponderacion'] for c in data['criterios'])
        if abs(total_ponderacion - 100) > 0.01:
            return jsonify({'error': f'El total de porcentajes debe ser 100%. Actual: {total_ponderacion}%'}), 400

        nuevo_trabajo = TrabajoFactory.crear_trabajo(
            tipo=data['tipo'],
            titulo=data['titulo'],
            estudiante_id=data['estudiante_id']
        )
        db.session.add(nuevo_trabajo)
        db.session.flush()  

        for criterio_data in data['criterios']:
            criterio = Criterio(
                nombre=criterio_data['nombre'],
                ponderacion=criterio_data['ponderacion'],
                trabajo_id=nuevo_trabajo.id,
                descripcion=criterio_data.get('descripcion', '')
            )
            db.session.add(criterio)

        db.session.commit()
        return jsonify({'mensaje': 'Trabajo y criterios agregados correctamente'})
    except ValueError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al crear trabajo: {str(e)}'}), 500

@app.route('/editar_trabajo/<int:trabajo_id>')
def editar_trabajo(trabajo_id):
    trabajo = Trabajo.query.get_or_404(trabajo_id)
    estudiantes = Estudiante.query.all()
    criterios = Criterio.query.filter_by(trabajo_id=trabajo_id).all()
    return render_template('editar_trabajo.html', trabajo=trabajo, estudiantes=estudiantes, criterios=criterios, Estudiante=Estudiante)

@app.route('/actualizar_trabajo/<int:trabajo_id>', methods=['POST'])
def actualizar_trabajo(trabajo_id):
    trabajo = Trabajo.query.get_or_404(trabajo_id)
    trabajo.titulo = request.form['titulo']
    trabajo.tipo = request.form['tipo']
    trabajo.estudiante_id = request.form['estudiante_id']
    db.session.commit()
    return redirect('/panel/trabajos')

@app.route('/eliminar_trabajo/<int:trabajo_id>')
def eliminar_trabajo(trabajo_id):

    try:
        trabajo = Trabajo.query.get_or_404(trabajo_id)

        Evaluacion.query.filter_by(trabajo_id=trabajo_id).delete()

        Criterio.query.filter_by(trabajo_id=trabajo_id).delete()

        db.session.delete(trabajo)
        db.session.commit()

        return redirect('/panel/trabajos')
    except Exception as e:
        db.session.rollback()
        return f"Error al eliminar el trabajo: {str(e)}", 500

@app.route('/panel/evaluaciones')
def panel_evaluaciones():
    evaluaciones = Evaluacion.query.all()
    criterios = Criterio.query.all()

    notas_por_trabajo = {}
    for ev in evaluaciones:
        crit = next((c for c in criterios if c.id == ev.criterio_id), None)
        if crit:
            if ev.trabajo_id not in notas_por_trabajo:
                notas_por_trabajo[ev.trabajo_id] = {'total': 0, 'peso': 0}
            notas_por_trabajo[ev.trabajo_id]['total'] += ev.nota * crit.ponderacion
            notas_por_trabajo[ev.trabajo_id]['peso'] += crit.ponderacion

    notas_finales = {
        tid: round(data['total'] / data['peso'], 2) if data['peso'] > 0 else 'N/A'
        for tid, data in notas_por_trabajo.items()
    }

    return render_template('panel_evaluaciones.html',
                           evaluaciones=evaluaciones,
                           criterios=criterios,
                           notas_finales=notas_finales,
                           Trabajo=Trabajo,
                           Estudiante=Estudiante,
                           Criterio=Criterio)

@app.route('/agregar_evaluacion/<int:trabajo_id>')
def agregar_evaluacion_form(trabajo_id):
    trabajo = Trabajo.query.get(trabajo_id)
    estudiante = Estudiante.query.get(trabajo.estudiante_id)
    criterios = Criterio.query.filter_by(trabajo_id=trabajo_id).all()
    return render_template('agregar_evaluacion.html', trabajo=trabajo, estudiante=estudiante, criterios=criterios)

@app.route('/guardar_evaluacion/<int:trabajo_id>', methods=['POST'])
def guardar_evaluacion(trabajo_id):
    trabajo = Trabajo.query.get(trabajo_id)
    if not trabajo:
        return "Trabajo no encontrado", 404

    criterios = Criterio.query.filter_by(trabajo_id=trabajo_id).all()

    for criterio in criterios:
        key = f'nota_{criterio.id}'
        nota_str = request.form.get(key)
        if nota_str:
            nota = float(nota_str)

            if nota < 0 or nota > 100:
                return f"La nota para {criterio.nombre} debe estar entre 0 y 100", 400

            evaluacion = Evaluacion.query.filter_by(
                trabajo_id=trabajo.id,
                criterio_id=criterio.id
            ).first()

            if evaluacion:
                evaluacion.nota = nota
            else:
                nueva = Evaluacion(
                    trabajo_id=trabajo.id,
                    criterio_id=criterio.id,
                    nota=nota
                )
                db.session.add(nueva)

    db.session.commit()
    return redirect(f'/panel/trabajos/{trabajo_id}')

@app.route('/editar_evaluacion/<int:evaluacion_id>')
def editar_evaluacion(evaluacion_id):
    evaluacion = Evaluacion.query.get_or_404(evaluacion_id)
    trabajo = Trabajo.query.get(evaluacion.trabajo_id)
    criterio = Criterio.query.get(evaluacion.criterio_id)
    return render_template('editar_evaluacion.html', evaluacion=evaluacion, trabajo=trabajo, criterio=criterio)

@app.route('/actualizar_evaluacion/<int:evaluacion_id>', methods=['POST'])
def actualizar_evaluacion(evaluacion_id):
    evaluacion = Evaluacion.query.get_or_404(evaluacion_id)
    evaluacion.nota = float(request.form['nota'])
    db.session.commit()
    return redirect('/panel/evaluaciones')

@app.route('/eliminar_evaluacion/<int:evaluacion_id>')
def eliminar_evaluacion(evaluacion_id):
    evaluacion = Evaluacion.query.get_or_404(evaluacion_id)
    db.session.delete(evaluacion)
    db.session.commit()
    return redirect('/panel/evaluaciones')

@app.route('/historial_actas/<int:estudiante_id>')
def historial_actas(estudiante_id):
    estudiante = Estudiante.query.get(estudiante_id)
    if not estudiante:
        return "Estudiante no encontrado", 404

    trabajos = Trabajo.query.filter_by(estudiante_id=estudiante_id).all()
    criterios = Criterio.query.all()
    estrategia = CalculoLineal()

    historial = []
    for trabajo in trabajos:
        evaluaciones = Evaluacion.query.filter_by(trabajo_id=trabajo.id).all()
        resultado = []
        promedio_final = 0

        for e in evaluaciones:
            criterio = next((c for c in criterios if c.id == e.criterio_id), None)
            if criterio:
                aporte = estrategia.calcular_aporte(e.nota, criterio.ponderacion)
                resultado.append({
                    'criterio': criterio.nombre,
                    'nota': e.nota,
                    'aporte': round(aporte, 2)
                })
                promedio_final += aporte

        historial.append({
            'trabajo': trabajo,
            'evaluaciones': resultado,
            'promedio': round(promedio_final, 2)
        })

    return render_template('secciones/historial_actas.html', estudiante=estudiante, historial=historial)

@app.route('/generar_acta/<int:trabajo_id>')
def generar_acta(trabajo_id):

    trabajo = Trabajo.query.get(trabajo_id)
    if not trabajo:
        return jsonify({'error': 'Trabajo no encontrado'}), 404

    estudiante = Estudiante.query.get(trabajo.estudiante_id)
    
    class Evaluador:
        def __init__(self):
            self.nombre = "Administrador"
    
    evaluador = Evaluador()

    evaluaciones = Evaluacion.query.filter_by(trabajo_id=trabajo_id).all()
    criterios = Criterio.query.filter_by(trabajo_id=trabajo_id).all()
    estrategia = CalculoLineal()

    resultado = []
    promedio_final = 0

    for criterio in criterios:
        evaluacion = next((e for e in evaluaciones if e.criterio_id == criterio.id), None)
        
        if evaluacion:
            aporte = estrategia.calcular_aporte(evaluacion.nota, criterio.ponderacion)
            resultado.append({
                'criterio': criterio.nombre,
                'nota': evaluacion.nota,
                'aporte': round(aporte, 2)
            })
            promedio_final += aporte
        else:
            resultado.append({
                'criterio': criterio.nombre,
                'nota': 'Sin nota',
                'aporte': 0
            })

    generador = ActaPDF()
    pdf_bytes = generador.generar_acta(trabajo, resultado, round(promedio_final, 2), estudiante, evaluador)

    return Response(pdf_bytes, mimetype='application/pdf',
                    headers={"Content-Disposition": f"inline; filename=acta_{trabajo_id}.pdf"})

@app.route('/seccion/configuracion')
def cargar_configuracion():
    config = ConfiguracionGlobal()
    return render_template('secciones/configuracion.html', config=config)

@app.route('/actualizar_configuracion', methods=['POST'])
def actualizar_configuracion():
    config = ConfiguracionGlobal()
    config.institucion = request.form['institucion']
    config.escala_notas = request.form['escala_notas']
    config.formato_acta = request.form['formato_acta']
    return redirect('/seccion/configuracion')

if __name__ == '__main__':
    app.run(debug=True)
