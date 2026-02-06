from flask import Flask, render_template, request, redirect, url_for, flash
from flask_mysqldb import MySQL
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask import send_from_directory
from werkzeug.utils import secure_filename
from functools import wraps
import keras  
from tensorflow.keras.preprocessing import image
import numpy as np
import os
from collections import Counter
from config import config
from models.ModelUser import ModelUser
from models.entities.User import User

# --------------------------------------------
# DECORADOR PARA CONTROL DE ACCESO
# --------------------------------------------
def admin_required(f):

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Debes iniciar sesión para acceder', 'warning')
            return redirect(url_for('login'))
        
        if not current_user.is_admin():
            flash(' Acceso denegado. Solo administradores pueden acceder a esta sección.', 'danger')
            return redirect(url_for('home'))
        
        return f(*args, **kwargs)
    return decorated_function

# --------------------------------------------
# CONFIGURACIÓN DE RUTAS
# --------------------------------------------
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SRC_DIR)

# --------------------------------------------
# CONFIGURACIÓN PRINCIPAL
# --------------------------------------------
app = Flask(__name__, 
            static_folder=os.path.join(SRC_DIR, 'static'),
            template_folder=os.path.join(SRC_DIR, 'templates'))

csrf = CSRFProtect()
db = MySQL(app)
login_manager_app = LoginManager(app)
login_manager_app.login_view = 'login'

UPLOAD_FOLDER = os.path.join(SRC_DIR, 'static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_IMAGES'] = 10

MODEL_PATH = os.path.join(BASE_DIR, 'modelo_plagas_palta.keras')  

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

if os.path.exists(MODEL_PATH):
    model = keras.models.load_model(MODEL_PATH)  
    print(f" Modelo cargado desde: {MODEL_PATH}")
else:
    model = None
    print(f" Modelo no encontrado en: {MODEL_PATH}")


class_names = ['Huevos', 'No Relacionado', 'Palta Dañada', 'Palta Sana','Plaga']

class_descriptions = {
    'Plaga': 'Se ha detectado la presencia de plagas (insectos) en la planta. '
             'Esto incluye trips, chinches u otros insectos que pueden dañar hojas, tallos y frutos.',
    
    'Huevos': 'Se han identificado huevecillos de plagas. Estos son indicadores tempranos '
              'de una posible infestación futura. Es crucial actuar rápidamente.',
    
    'Palta Sana': '¡Excelente! El fruto se encuentra en perfecto estado. '
                  'No se detectan signos de plagas ni daños.',
    
    'Palta Dañada': 'El fruto presenta daños visibles, posiblemente causados por plagas, '
                    'enfermedades o factores ambientales.',
    
    'No Relacionado': 'La imagen no corresponde a paltas ni plagas relacionadas. '
                      'Por favor, sube una imagen del cultivo de palta para análisis.'
}

care_instructions = {
    'Plaga': '- TRATAMIENTO INMEDIATO:\n'
             '• Aplicar insecticida orgánico (aceite de neem al 2%)\n'
             '• Realizar fumigación temprano en la mañana o al atardecer\n'
             '• Repetir aplicación cada 7-10 días por 3 semanas\n'
             '• Monitorear plantas vecinas\n'
             '• Mejorar ventilación del cultivo',
    
    'Huevos': '- PREVENCIÓN Y CONTROL:\n'
              '• Remover manualmente los huevos encontrados\n'
              '• Aplicar jabón potásico diluido (1-2%)\n'
              '• Inspeccionar envés de hojas semanalmente\n'
              '• Introducir enemigos naturales (crisopas, mariquitas)\n'
              '• Evitar exceso de nitrógeno en fertilización',
    
    'Palta Sana': '- MANTENIMIENTO PREVENTIVO:\n'
                  '• Continuar con programa de monitoreo semanal\n'
                  '• Mantener buenas prácticas de riego\n'
                  '• Aplicar fertilización balanceada\n'
                  '• Limpiar malezas alrededor del cultivo\n'
                  '• Inspección visual cada 3-4 días',
    
    'Palta Dañada': '- MANEJO DEL FRUTO DAÑADO:\n'
                    '• Remover frutos severamente dañados\n'
                    '• Evaluar causa del daño (plaga, hongo, mecánico)\n'
                    '• Si es por plaga: aplicar tratamiento específico\n'
                    '• Mejorar manejo cultural (poda, ventilación)\n'
                    '• Considerar cosecha anticipada si es viable',
    
    'No Relacionado': '- ACCIÓN REQUERIDA:\n'
                      '• Verificar que la imagen sea del cultivo de palta\n'
                      '• Asegurarse de enfocar en frutos, hojas o plagas\n'
                      '• Evitar fondos con otros objetos o personas\n'
                      '• Tomar fotos con buena iluminación\n'
                      '• Intentar nuevamente con imagen apropiada'
}

severity_levels = {
    'Plaga': 'ALTO - Requiere acción inmediata',
    'Huevos': 'MEDIO - Actuar en 24-48 horas',
    'Palta Sana': 'NINGUNO - Continuar monitoreo',
    'Palta Dañada': 'MEDIO-ALTO - Evaluar y actuar',
    'No Relacionado': 'N/A - Imagen no válida'
}

additional_recommendations = {
    'Plaga': '- IMPORTANTE:\n'
             '• Registrar ubicación de plantas afectadas\n'
             '• Verificar condiciones climáticas favorables para plagas\n'
             '• Considerar trampas cromáticas (amarillas o azules)\n'
             '• Consultar a un ingeniero agrónomo si la infestación persiste\n'
             '• Documentar con fotos para seguimiento',
    
    'Huevos': '- SEGUIMIENTO:\n'
              '• Marcar las plantas afectadas\n'
              '• Revisar cada 2-3 días\n'
              '• Fotografiar para comparar evolución\n'
              '• Implementar control biológico preventivo\n'
              '• Capacitar al personal en identificación de huevos',
    
    'Palta Sana': '- BUENAS PRÁCTICAS:\n'
                  '• Mantener registro fotográfico del estado sano\n'
                  '• Continuar con el calendario de fertilización\n'
                  '• Revisar sistema de riego periódicamente\n'
                  '• Realizar poda sanitaria cuando sea necesario\n'
                  '• Mantener limpio el área de cultivo',
    
    'Palta Dañada': '- ANÁLISIS:\n'
                    '• Determinar si el daño es progresivo o detenido\n'
                    '• Evaluar porcentaje de frutos afectados\n'
                    '• Revisar historial de tratamientos previos\n'
                    '• Tomar muestras si hay sospecha de enfermedad\n'
                    '• Ajustar calendario de aplicaciones preventivas',
    
    'No Relacionado': '- RECOMENDACIONES:\n'
                      '• Usar el sistema solo para análisis de paltas\n'
                      '• Tomar fotos cercanas del área a analizar\n'
                      '• Evitar incluir objetos ajenos al cultivo\n'
                      '• Asegurar buena iluminación natural\n'
                      '• Si persiste, consultar con soporte técnico'
}

# --------------------------------------------
# LOGIN
# --------------------------------------------
@login_manager_app.user_loader
def load_user(id):
    return ModelUser.get_by_id(db, id)

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User(0, request.form['username'], request.form['password'])
        logged_user = ModelUser.login(db, user)
        if logged_user:
            if logged_user.password:
                login_user(logged_user)
                return redirect(url_for('home'))
            else:
                flash("Contraseña incorrecta.")
        else:
            flash("Usuario no encontrado.")
    return render_template('auth/login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# --------------------------------------------
# FUNCION PARA PROCESAR IMAGENES
# --------------------------------------------
def procesar_multiples_imagenes(files):
    """Procesa múltiples imágenes y genera resultado por votacion"""
    resultados = []
    filenames = []
    
    for file in files:
        try:
            filename_safe = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename_safe)
            file.save(filepath)
            filenames.append(filename_safe)
            
            img = image.load_img(filepath, target_size=(224, 224))
            img_array = image.img_to_array(img) / 255.0
            img_array = np.expand_dims(img_array, axis=0)
            
            predictions = model.predict(img_array, verbose=0)
            predicted_index = np.argmax(predictions[0])
            predicted_class = class_names[predicted_index]
            probability = float(np.max(predictions[0])) * 100
            
            resultados.append({
                'filename': filename_safe,
                'class': predicted_class,
                'probability': probability,
                'index': predicted_index,
                'all_probabilities': predictions[0].tolist()
            })
            
            print(f" {filename_safe}: {predicted_class} ({probability:.2f}%)")
            
        except Exception as e:
            print(f" Error en {file.filename}: {e}")
            continue
    
    if not resultados:
        return None
    
    return calcular_consenso_por_votacion(resultados, filenames)


def calcular_consenso_por_votacion(resultados, filenames):

    total_imagenes = len(resultados)
    
  
    clases = [r['class'] for r in resultados]
    conteo_clases = Counter(clases)
    
    
    clase_ganadora = conteo_clases.most_common(1)[0][0]
    votos_ganadora = conteo_clases[clase_ganadora]
    
    
    porcentaje_mayoria = (votos_ganadora / total_imagenes) * 100
    
    if porcentaje_mayoria >= 80:
        nivel_confianza = "MUY ALTA"
        confianza_final = 95.0
    elif porcentaje_mayoria >= 70:
        nivel_confianza = "ALTA"
        confianza_final = 85.0
    elif porcentaje_mayoria > 50:
        nivel_confianza = "MODERADA"
        confianza_final = 75.0
    elif porcentaje_mayoria == 50:
        nivel_confianza = "BAJA - Empate"
        confianza_final = 50.0
    else:
        nivel_confianza = "BAJA - No hay mayoría"
        confianza_final = 40.0
    
    probabilidades_clase_ganadora = [
        r['probability'] for r in resultados if r['class'] == clase_ganadora
    ]
    promedio_probabilidades = np.mean(probabilidades_clase_ganadora)
    
    tiene_contradiccion = len(set(clases)) > 1
    
    detalles_por_clase = {}
    for clase in set(clases):
        imgs_clase = [r for r in resultados if r['class'] == clase]
        detalles_por_clase[clase] = {
            'count': len(imgs_clase),
            'percentage': (len(imgs_clase) / total_imagenes) * 100,
            'avg_prob': np.mean([r['probability'] for r in imgs_clase]),
            'filenames': [r['filename'] for r in imgs_clase]
        }
    
    if porcentaje_mayoria > 50:
        mensaje_interpretacion = (
            f"✓ {votos_ganadora} de {total_imagenes} imágenes "
            f"({porcentaje_mayoria:.0f}%) coinciden en '{clase_ganadora}'. "
            f"Confianza: {nivel_confianza}"
        )
    elif porcentaje_mayoria == 50:
        mensaje_interpretacion = (
            f"⚠ Empate: {votos_ganadora}/{total_imagenes} imágenes. "
            f"Resultado incierto. Se recomienda análisis manual."
        )
    else:
        mensaje_interpretacion = (
            f"⚠ No hay mayoría clara. "
            f"La clase más común es '{clase_ganadora}' con {votos_ganadora}/{total_imagenes} votos."
        )
    
    return {
        'predicted_class': clase_ganadora,
        'probability': round(confianza_final, 2),
        'nivel_confianza': nivel_confianza,
        'raw_probability': round(promedio_probabilidades, 2),
        'consensus_percentage': round(porcentaje_mayoria, 2),
        'total_images': total_imagenes,
        'votes': votos_ganadora,
        'has_contradiction': tiene_contradiccion,
        'mensaje_interpretacion': mensaje_interpretacion,
        'all_results': resultados,
        'details_by_class': detalles_por_clase,
        'filenames': filenames
    }


# --------------------------------------------
# RUTA PRINCIPAL
# --------------------------------------------
@app.route('/home', methods=['GET', 'POST'])
@login_required
def home():
    if request.method == 'POST':
        print("=" * 60)
        print(" ANÁLISIS POR VOTACION MAYORITARIA")
        print("=" * 60)
        
        if model is None:
            flash(" El modelo aún no esta entrenado.")
            return redirect(url_for('home'))
        
        files = request.files.getlist('files')
        
        if not files or all(f.filename == '' for f in files):
            flash(" Por favor selecciona al menos una imagen.")
            return redirect(url_for('home'))
        
        if len(files) > app.config['MAX_IMAGES']:
            flash(f" Máximo {app.config['MAX_IMAGES']} imágenes permitidas.")
            return redirect(url_for('home'))
        
        try:
            resultado = procesar_multiples_imagenes(files)
            
            if resultado is None:
                flash(" Error al procesar las imágenes.")
                return redirect(url_for('home'))
            
            print(f"\n{resultado['mensaje_interpretacion']}")
            print(f"Confianza por mayoría: {resultado['probability']}%")
            print(f"Promedio probabilidades: {resultado['raw_probability']}%")
            print("=" * 60 + "\n")
            
            return render_template(
                'home.html',
                current_user=current_user,
                resultado=resultado,
                predicted_class=resultado['predicted_class'],
                probability=resultado['probability'],
                description=class_descriptions.get(resultado['predicted_class'], ""),
                instructions=care_instructions.get(resultado['predicted_class'], ""),
                severity=severity_levels.get(resultado['predicted_class'], ""),
                recommendations=additional_recommendations.get(resultado['predicted_class'], "")
            )
            
        except Exception as e:
            print(f" ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            flash(f" Error: {str(e)}")
            return redirect(url_for('home'))

    return render_template('home.html', current_user=current_user)


@app.route('/uploads/<filename>')
@login_required
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/usuarios')
@login_required
@admin_required  
def usuarios():
    try:
        usuarios = ModelUser.get_all(db)
        return render_template('usuarios/lista.html', usuarios=usuarios)
    except Exception as ex:
        flash(f"Error: {str(ex)}", "danger")
        return redirect(url_for('home'))


@app.route('/usuarios/nuevo', methods=['GET', 'POST'])
@login_required
@admin_required   
def usuario_nuevo():
    
    if request.method == 'POST':
        try:
            username = request.form['username']
            password = request.form['password']
            fullname = request.form['fullname']
            role = request.form.get('role', 'usuario')   
            
            
            if not username or not password:
                flash("Usuario y contraseña son obligatorios", "warning")
                return redirect(url_for('usuario_nuevo'))
            
            if len(password) < 6:
                flash("La contraseña debe tener al menos 6 caracteres", "warning")
                return redirect(url_for('usuario_nuevo'))
            
             
            if ModelUser.username_exists(db, username):
                flash("El usuario ya existe", "warning")
                return redirect(url_for('usuario_nuevo'))
            
           
            nuevo_usuario = User(0, username, None, fullname, role)
            user_id = ModelUser.create(db, nuevo_usuario, password)
            
            flash(f"Usuario '{username}' creado exitosamente como {role}", "success")
            return redirect(url_for('usuarios'))
            
        except Exception as ex:
            flash(f"Error al crear usuario: {str(ex)}", "danger")
            return redirect(url_for('usuario_nuevo'))
    
    return render_template('usuarios/form.html', usuario=None, accion='Crear')


@app.route('/usuarios/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required   
def usuario_editar(id):   
    if request.method == 'POST':
        try:
            username = request.form['username']
            password = request.form.get('password', '').strip()
            fullname = request.form['fullname']
            role = request.form.get('role', 'usuario')   
            
             
            if not username:
                flash("El usuario es obligatorio", "warning")
                return redirect(url_for('usuario_editar', id=id))
            
            
            if ModelUser.username_exists(db, username, exclude_id=id):
                flash("El usuario ya existe", "warning")
                return redirect(url_for('usuario_editar', id=id))
            
            
            if password and len(password) < 6:
                flash("La contraseña debe tener al menos 6 caracteres", "warning")
                return redirect(url_for('usuario_editar', id=id))
            
             
            usuario_actual = ModelUser.get_by_id(db, id)
            if usuario_actual.role == 'administrador' and role != 'administrador':
                admin_count = ModelUser.count_admins(db)
                if admin_count <= 1:
                    flash("No puedes cambiar el rol del último administrador", "danger")
                    return redirect(url_for('usuario_editar', id=id))
            
            
            usuario = User(id, username, None, fullname, role)
            
            if password:
                ModelUser.update(db, usuario, password)
                flash(f"Usuario '{username}' actualizado (con nueva contraseña)", "success")
            else:
                ModelUser.update(db, usuario)
                flash(f"Usuario '{username}' actualizado", "success")
            
            return redirect(url_for('usuarios'))
            
        except Exception as ex:
            flash(f"Error al actualizar: {str(ex)}", "danger")
            return redirect(url_for('usuario_editar', id=id))
    
     
    try:
        usuario = ModelUser.get_by_id(db, id)
        if not usuario:
            flash("Usuario no encontrado", "danger")
            return redirect(url_for('usuarios'))
        
        return render_template('usuarios/form.html', usuario=usuario, accion='Editar')
    except Exception as ex:
        flash(f"Error: {str(ex)}", "danger")
        return redirect(url_for('usuarios'))


@app.route('/usuarios/eliminar/<int:id>', methods=['POST'])
@login_required
@admin_required  
def usuario_eliminar(id):
    
    try:
       
        if current_user.id == id:
            flash("No puedes eliminar tu propio usuario", "warning")
            return redirect(url_for('usuarios'))
             
        usuario = ModelUser.get_by_id(db, id)
               
        if usuario.role == 'administrador':
            admin_count = ModelUser.count_admins(db)
            if admin_count <= 1:
                flash("No puedes eliminar el único administrador del sistema", "danger")
                return redirect(url_for('usuarios'))
        
        if ModelUser.delete(db, id):
            flash(f"Usuario '{usuario.username}' eliminado", "success")
        else:
            flash("No se pudo eliminar el usuario", "warning")
            
    except Exception as ex:
        flash(f"Error al eliminar: {str(ex)}", "danger")
    
    return redirect(url_for('usuarios'))


def status_401(error):
    return redirect(url_for('login'))

def status_404(error):
    return "<h1>Página no encontrada</h1>", 404


if __name__ == '__main__':
    app.config.from_object(config['development'])
    csrf.init_app(app)
    app.register_error_handler(401, status_401)
    app.register_error_handler(404, status_404)
    
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    print("\n" + "="*60)
    print(" SISTEMA DE DETECCIÓN POR VOTACIÓN MAYORITARIA")
    print("="*60)
    if model is not None:
        print(f" Modelo cargado: {MODEL_PATH}")
        print(f" Método: Votacion (NO promedio)")
        print(f" Imagenes: 1-{app.config['MAX_IMAGES']}")
        print(f" Logica: >50% = Alta confianza")
        print(f" Sistema de roles: ACTIVADO")
    else:
        print(f" Modelo NO encontrado")
    print("="*60 + "\n")
    
    app.run(debug=True)