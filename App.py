from flask import Flask, render_template, request, redirect, url_for, session, flash, make_response
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_socketio import SocketIO
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo
from flask_migrate import Migrate
from io import BytesIO
import os
from flask import send_file
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import qrcode
from sqlalchemy import func
from datetime import datetime



app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///agencia.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SESSION_TYPE'] = 'filesystem'

# Rutas para archivos estáticos y plantillas
app.static_folder = 'static'
app.template_folder = 'templates'



db = SQLAlchemy(app)
socketio = SocketIO(app)

migrate = Migrate(app, db)
HCAPTCHA_SECRET = 'ES_279a0ffcd1dc48a083fd950d56a243d0' 

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre_usuario = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

class LoginForm(FlaskForm):
    usuario = StringField('Usuario', validators=[DataRequired()])
    contrasena = PasswordField('Contraseña', validators=[DataRequired()])
    submit = SubmitField('Login')

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Length

class RegistroClienteForm(FlaskForm):
    nombre_usuario = StringField('Nombre de Usuario', validators=[DataRequired(), Length(min=4, max=25)])
    password = PasswordField('Contraseña', validators=[DataRequired(), Length(min=6)])


class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    curp = db.Column(db.String(18), nullable=False)
    turno_numero = db.Column(db.Integer, nullable=False)
    nombre_completo = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(15), nullable=True)  # Nuevo campo
    celular = db.Column(db.String(15), nullable=True)   # Nuevo campo
    correo = db.Column(db.String(100), nullable=True)   # Nuevo campo
    nivel = db.Column(db.Enum('primaria', 'secundaria', 'preparatoria', 'universidad'), nullable=False)  # Nuevo campo
    municipio = db.Column(db.Enum('saltillo', 'arteaga', 'ramos arizpe'), nullable=False)  # Nuevo campo
    asunto = db.Column(db.Enum('inscripcion', 'informacion', 'otros'), nullable=False)     # Nuevo campo
    fecha_registro = db.Column(db.DateTime, nullable=False, default=datetime.now)
    qr_code = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    def __init__(self, curp, turno_numero, nombre_completo, telefono=None, celular=None, correo=None, nivel=None, municipio=None, asunto=None, qr_code=None):
        self.curp = curp
        self.turno_numero = turno_numero
        self.nombre_completo = nombre_completo
        self.telefono = telefono
        self.celular = celular
        self.correo = correo
        self.nivel = nivel
        self.municipio = municipio
        self.asunto = asunto
        self.qr_code = qr_code
    
    def generar_numero_turno(self):
        # Obtener el último número de turno registrado
        ultimo_ticket = Ticket.query.order_by(Ticket.id.desc()).first()
        if ultimo_ticket:
            return ultimo_ticket.turno_numero + 1
        else:
            return 1





@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login_admin', methods=['GET', 'POST'])
def login_admin():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.usuario.data
        password = form.contrasena.data
        if username == 'admin' and password == 'contraseña_admin':
            session['is_admin'] = True
            return redirect(url_for('ticket_admin'))
        else:
            flash('Credenciales incorrectas. Inténtalo de nuevo.', 'danger')
    return render_template('login_admin.html', form=form)

@app.route('/login_cliente', methods=['GET', 'POST'])
def login_cliente():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cliente = Cliente.query.filter_by(nombre_usuario=username).first()
        if cliente and check_password_hash(cliente.password, password):
            session['cliente_logged_in'] = True
            return redirect(url_for('ticket_cliente'))
        else:
            flash('Usuario o contraseña incorrectos. Inténtalo de nuevo.', 'danger')
    return render_template('login_cliente.html')

@app.route('/ticket_admin')
def ticket_admin():
    if session.get('is_admin'):
        return render_template('ticket_admin.html')
    else:
        flash('Acceso no autorizado.', 'danger')
        return redirect(url_for('login_admin'))

@app.route('/logout_admin', methods=['POST'])
def logout_admin():
    session.pop('admin_logged_in', None)
    return redirect(url_for('home'))



@app.route('/ticket_cliente')
def ticket_cliente():
    if session.get('cliente_logged_in'):
        return render_template('ticket_cliente.html')
    else:
        flash('Debes iniciar sesión para acceder a esta página.', 'danger')
        return redirect(url_for('login_cliente'))


@app.route('/logout', methods=['POST'])
def logout():
    session.pop('cliente_logged_in', None)
    return redirect(url_for('home'))



@app.route('/registro_cliente', methods=['GET', 'POST'])
def registro_cliente():
    form = RegistroClienteForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256')
        nuevo_cliente = Cliente(nombre_usuario=form.nombre_usuario.data, password=hashed_password)
        try:
            db.session.add(nuevo_cliente)
            db.session.commit()
            flash('¡Registro exitoso! Ahora puedes iniciar sesión como cliente.', 'success')
            return redirect(url_for('login_cliente'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error al registrar cliente: {e}", 'danger')
    return render_template('registro_cliente.html', form=form)


@app.route('/registrar_ticket', methods=['POST'])
def registrar_ticket():
    curp = request.form.get('curp')
    nombre_completo = request.form.get('nombre_completo')
    telefono = request.form.get('telefono')
    celular = request.form.get('celular')
    correo = request.form.get('correo')
    nivel = request.form.get('nivel')
    municipio = request.form.get('municipio')
    asunto = request.form.get('asunto')

    if not curp or not nombre_completo or not nivel or not municipio or not asunto:
        flash('Todos los campos son obligatorios.', 'error')
        return redirect(url_for('ticket_cliente'))

    try:
        ticket = Ticket(curp=curp, nombre_completo=nombre_completo, telefono=telefono, celular=celular, correo=correo, nivel=nivel, municipio=municipio, asunto=asunto)
        db.session.add(ticket)
        db.session.commit()
        flash('Ticket registrado correctamente.', 'success')
        return redirect(url_for('registro_terminado_cliente'))  # Redirige a registro_terminado_cliente.html después de registrar el ticket
    except Exception as e:
        db.session.rollback()
        flash(f'Error al registrar el ticket: {str(e)}', 'error')
        return redirect(url_for('ticket_cliente'))


@app.route('/registrar_ticket_admin', methods=['POST'])
def registrar_ticket_admin():
    if request.method == 'POST':
        curp = request.form['curp']
        nombre_completo = request.form['nombre_completo']
        nombre = request.form['nombre']
        paterno = request.form['paterno']
        materno = request.form['materno']
        telefono = request.form['telefono']
        celular = request.form['celular']
        correo = request.form['correo']
        nivel = request.form['nivel']
        municipio = request.form['municipio']
        asunto = request.form['asunto']
        
        # Obtener el último número de turno registrado
        ultimo_ticket = Ticket.query.order_by(Ticket.id.desc()).first()
        if ultimo_ticket:
            nuevo_numero_turno = ultimo_ticket.turno_numero + 1
        else:
            nuevo_numero_turno = 1
        
        # Guardar el ticket en la base de datos
        nuevo_ticket = Ticket(
            curp=curp, 
            turno_numero=nuevo_numero_turno, 
            nombre_completo=nombre_completo,
            nombre=nombre,
            paterno=paterno,
            materno=materno,
            telefono=telefono,
            celular=celular,
            correo=correo,
            nivel=nivel,
            municipio=municipio,
            asunto=asunto
        )
        db.session.add(nuevo_ticket)
        db.session.commit()

        return redirect(url_for('registro_terminado_admin')) 

@app.route('/registro_terminado_admin', methods=['GET'])
def registro_terminado_admin():
    # Aquí obtén el último ticket registrado o como lo necesites
    ultimo_ticket = Ticket.query.order_by(Ticket.id.desc()).first()
    
    # Asegúrate de que `ticket` esté disponible en el contexto de la plantilla
    return render_template('registro_terminado_admin.html', ticket=ultimo_ticket)


@app.route('/registro_terminado', methods=['GET'])
def registro_terminado():
    # Aquí obtén el último ticket registrado o como lo necesites
    ultimo_ticket = Ticket.query.order_by(Ticket.id.desc()).first()
    
    # Asegúrate de que `ticket` esté disponible en el contexto de la plantilla
    return render_template('registro_terminado_cliente.html', ticket=ultimo_ticket)

@app.route('/registro_terminado_cliente')
def registro_terminado_cliente():
    return render_template('registro_terminado_cliente.html')


import os

def generar_pdf(ticket_id):
    # Obtener el ticket de la base de datos
    ticket = Ticket.query.get(ticket_id)
    if not ticket:
        return None
    
    # Crear un objeto PDF
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    
    # Configurar el contenido del PDF
    c.drawString(100, 750, "¡Ticket de Turno!")
    c.drawString(100, 730, f"Nombre: {ticket.nombre_completo}")
    c.drawString(100, 710, f"CURP: {ticket.curp}")
    c.drawString(100, 690, f"Número de Turno: {ticket.turno_numero}")

    # Generar y guardar el código QR
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(f"Nombre: {ticket.nombre_completo}, CURP: {ticket.curp}, Número de Turno: {ticket.turno_numero}")
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    # Verificar si el directorio `static/qr_codes` existe, si no, crearlo
    qr_codes_dir = os.path.join(app.static_folder, 'qr_codes')
    if not os.path.exists(qr_codes_dir):
        os.makedirs(qr_codes_dir)

    qr_path = os.path.join(qr_codes_dir, f"qr_{ticket.id}.png")
    img.save(qr_path)  # Guardar el código QR como imagen

    # Ajustar la posición del código QR en el PDF
    c.drawImage(qr_path, 100, 550, width=100, height=100)  # Insertar el código QR en el PDF

    # Asegurarse de que el resto de los datos del ticket se muestran correctamente
    c.drawString(100, 530, "Detalles del Ticket:")
    c.drawString(100, 510, f"Nombre Completo: {ticket.nombre_completo}")
    c.drawString(100, 490, f"CURP: {ticket.curp}")
    c.drawString(100, 470, f"Número de Turno: {ticket.turno_numero}")

    c.showPage()
    c.save()
    
    pdf_data = buffer.getvalue()
    buffer.close()
    
    return pdf_data


@app.route('/generar_pdf', methods=['POST'])
def descargar_pdf():
    ticket_id = request.form.get('ticket_id')  # Obtener el ID del ticket desde el formulario

    # Generar el PDF y obtener los datos
    pdf_data = generar_pdf(ticket_id)
    
    if pdf_data:
        response = make_response(pdf_data)
        response.headers['Content-Disposition'] = 'attachment; filename=ticket.pdf'
        response.headers['Content-Type'] = 'application/pdf'
        return response
    else:
        flash('Error al generar el PDF.', 'danger')
        return redirect(url_for('registro_terminado'))

@app.route('/dashboard')
def dashboard():
    # Ejemplo de consulta SQLAlchemy
    ticket_counts = db.session.query(
        func.strftime('%Y-%m-%d', Ticket.fecha_registro),
        func.count(Ticket.id)
    ).group_by(func.strftime('%Y-%m-%d', Ticket.fecha_registro)).all()

    return render_template('dashboard.html', ticket_counts=ticket_counts)

@app.route('/modificar_ticket', methods=['GET', 'POST'])
def modificar_ticket():
    # Obtener todos los tickets registrados
    tickets = Ticket.query.all()
    return render_template('modificar_ticket.html', tickets=tickets)

# App.py

@app.route('/editar_ticket/<int:ticket_id>', methods=['GET', 'POST'])
def editar_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    if request.method == 'POST':
        ticket.nombre_completo = request.form['nombre_completo']
        ticket.curp = request.form['curp']
        ticket.telefono = request.form['telefono']
        ticket.celular = request.form['celular']
        ticket.correo = request.form['correo']
        ticket.nivel = request.form['nivel']
        ticket.municipio = request.form['municipio']
        ticket.asunto = request.form['asunto']
        # Agregar más campos según sea necesario
        
        db.session.commit()
        flash('Ticket actualizado correctamente.', 'success')
        return redirect(url_for('modificar_ticket'))
    return render_template('editar_ticket.html', ticket=ticket)


@app.route('/eliminar_ticket/<int:ticket_id>', methods=['POST'])
def eliminar_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    db.session.delete(ticket)
    db.session.commit()
    flash('Ticket eliminado correctamente.', 'success')
    return redirect(url_for('modificar_ticket'))


def guardar_ticket(curp, turno_numero, nombre_completo, qr_code=None):
    nuevo_ticket = Ticket(curp=curp, turno_numero=turno_numero, nombre_completo=nombre_completo, qr_code=qr_code)
    db.session.add(nuevo_ticket)
    db.session.commit()

@app.route('/todos_los_tickets', methods=['GET'])
def todos_los_tickets():
    tickets = Ticket.query.all()
    return render_template('modificar_ticket.html', tickets=tickets)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Imprime la lista de tablas
        print(db.engine.table_names())
    app.run(debug=True)
