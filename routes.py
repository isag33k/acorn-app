import logging
from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, EmailField, TextAreaField, SelectField, HiddenField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError

from app import app, db
from models import Equipment, CircuitMapping, User, UserCredential
from utils.ssh_client import SSHClient

logger = logging.getLogger(__name__)

# Login form
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

# Registration form
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = EmailField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    password2 = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    is_admin = BooleanField('Admin User')
    submit = SubmitField('Register')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Username already exists.')
            
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Email address already registered.')

# User credentials form
class UserCredentialForm(FlaskForm):
    equipment_id = HiddenField('Equipment ID', validators=[DataRequired()])
    username = StringField('Username', validators=[DataRequired(), Length(max=50)])
    password = PasswordField('Password', validators=[DataRequired(), Length(max=100)])
    submit = SubmitField('Save Credentials')

@app.route('/')
@login_required
def index():
    """Render the main page for alert submission"""
    # Create a form for CSRF protection
    form = FlaskForm()
    return render_template('index.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password', 'danger')
            return redirect(url_for('login'))
            
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or not next_page.startswith('/'):
            next_page = url_for('index')
        return redirect(next_page)
        
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    """User logout"""
    logout_user()
    return redirect(url_for('login'))

@app.route('/users')
@login_required
def user_list():
    """User management page (admin only)"""
    if not current_user.is_admin:
        flash('Admin access required', 'danger')
        return redirect(url_for('index'))
        
    users = User.query.all()
    form = RegistrationForm()
    return render_template('users.html', users=users, form=form)

@app.route('/users/add', methods=['POST'])
@login_required
def add_user():
    """Add a new user (admin only)"""
    if not current_user.is_admin:
        flash('Admin access required', 'danger')
        return redirect(url_for('index'))
        
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            is_admin=form.is_admin.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(f'User {form.username.data} registered successfully!', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{getattr(form, field).label.text}: {error}', 'danger')
                
    return redirect(url_for('user_list'))

@app.route('/users/delete/<int:id>', methods=['POST'])
@login_required
def delete_user(id):
    """Delete a user (admin only)"""
    if not current_user.is_admin:
        flash('Admin access required', 'danger')
        return redirect(url_for('index'))
        
    if current_user.id == id:
        flash('Cannot delete your own account', 'danger')
        return redirect(url_for('user_list'))
        
    user = User.query.get_or_404(id)
    db.session.delete(user)
    db.session.commit()
    
    flash(f'User {user.username} deleted successfully', 'success')
    return redirect(url_for('user_list'))

@app.route('/users/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_user(id):
    """Edit a user (admin only)"""
    if not current_user.is_admin:
        flash('Admin access required', 'danger')
        return redirect(url_for('index'))
        
    user = User.query.get_or_404(id)
    
    # Create a basic form for CSRF protection
    form = FlaskForm()
    
    if request.method == 'POST' and form.validate_on_submit():
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        is_admin = 'is_admin' in request.form
        
        # Check if username already exists
        if username != user.username and User.query.filter_by(username=username).first():
            flash(f'Username {username} already exists', 'danger')
            return redirect(url_for('edit_user', id=id))
            
        # Check if email already exists
        if email != user.email and User.query.filter_by(email=email).first():
            flash(f'Email {email} already registered', 'danger')
            return redirect(url_for('edit_user', id=id))
            
        user.username = username
        user.email = email
        user.is_admin = is_admin
        
        if password:
            user.set_password(password)
            
        db.session.commit()
        flash(f'User {username} updated successfully', 'success')
        return redirect(url_for('user_list'))
        
    return render_template('edit_user.html', user=user, form=form)

@app.route('/credentials', methods=['GET'])
@login_required
def user_credentials():
    """Manage user-specific credentials for equipment"""
    equipment = Equipment.query.all()
    user_credentials = UserCredential.query.filter_by(user_id=current_user.id).all()
    
    # Create a dict of existing credentials for easier access
    credentials_dict = {cred.equipment_id: cred for cred in user_credentials}
    
    # Create a single form for compatibility with the existing template
    form = UserCredentialForm()
    
    # Create a basic form for CSRF token in delete form
    csrf_form = FlaskForm()
    
    return render_template('credentials.html', equipment=equipment, credentials=credentials_dict, 
                          form=form, csrf_form=csrf_form)

@app.route('/credentials/add', methods=['POST'])
@login_required
def add_credential():
    """Add or update user credential for equipment"""
    # Create form for CSRF validation only
    form = FlaskForm()
    
    if form.validate_on_submit():
        # Get form data directly from request
        equipment_id = request.form.get('equipment_id')
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Basic validation
        if not equipment_id or not username or not password:
            flash('All fields are required', 'danger')
            return redirect(url_for('user_credentials'))
            
        # Check if credential already exists
        credential = UserCredential.query.filter_by(
            user_id=current_user.id,
            equipment_id=equipment_id
        ).first()
        
        if credential:
            # Update existing
            credential.username = username
            credential.password = password
            flash('Credential updated successfully', 'success')
        else:
            # Create new
            credential = UserCredential(
                user_id=current_user.id,
                equipment_id=equipment_id,
                username=username,
                password=password
            )
            db.session.add(credential)
            flash('Credential added successfully', 'success')
            
        db.session.commit()
    else:
        flash('CSRF validation failed', 'danger')
                
    return redirect(url_for('user_credentials'))

@app.route('/credentials/delete/<int:equipment_id>', methods=['POST'])
@login_required
def delete_credential(equipment_id):
    """Delete user credential for equipment"""
    # Validate CSRF token
    form = FlaskForm()
    if not form.validate_on_submit():
        flash('CSRF validation failed', 'danger')
        return redirect(url_for('user_credentials'))

    credential = UserCredential.query.filter_by(
        user_id=current_user.id,
        equipment_id=equipment_id
    ).first_or_404()
    
    db.session.delete(credential)
    db.session.commit()
    
    flash('Credential deleted successfully', 'success')
    return redirect(url_for('user_credentials'))

@app.route('/submit_alert', methods=['POST'])
@login_required
def submit_alert():
    """Process the submitted alert and run the SSH command(s)"""
    # Validate CSRF token
    form = FlaskForm()
    if not form.validate_on_submit():
        flash('CSRF token missing or invalid', 'danger')
        return redirect(url_for('index'))
        
    circuit_id = request.form.get('circuit_id', '').strip()
    
    if not circuit_id:
        flash('Please enter a circuit ID', 'danger')
        return redirect(url_for('index'))
    
    # Find circuit mappings for the given circuit ID
    mappings = CircuitMapping.query.filter_by(circuit_id=circuit_id).all()
    
    if not mappings:
        flash(f'No equipment mappings found for circuit ID: {circuit_id}', 'warning')
        return redirect(url_for('index'))
    
    results = []
    
    # Execute commands on each mapped equipment
    for mapping in mappings:
        equipment = mapping.equipment
        commands_list = mapping.get_commands_list()
        
        # If no valid commands, skip this mapping
        if not commands_list:
            logger.warning(f"No valid commands found for circuit {circuit_id} on {equipment.name}")
            continue
        
        try:
            # Get user-specific credentials for this equipment
            credentials = equipment.get_credentials_for_user(current_user)
            
            ssh_client = SSHClient(
                hostname=equipment.ip_address,
                port=equipment.ssh_port,
                username=credentials['username'],
                password=credentials['password']
            )
            
            # Connect to the equipment
            ssh_client.connect()
            
            # Execute each command and collect outputs
            for cmd in commands_list:
                output = ssh_client.execute_command(cmd)
                
                results.append({
                    'equipment_name': equipment.name,
                    'command': cmd,
                    'output': output,
                    'status': 'success'
                })
            
            # Disconnect after all commands are executed
            ssh_client.disconnect()
            
        except Exception as e:
            logger.error(f"SSH error for equipment {equipment.name}: {str(e)}")
            results.append({
                'equipment_name': equipment.name,
                'command': mapping.command,
                'output': str(e),
                'status': 'error'
            })
    
    return render_template('result.html', circuit_id=circuit_id, results=results)

@app.route('/equipment')
@login_required
def equipment_list():
    """List all equipment and circuit mappings"""
    equipment = Equipment.query.all()
    circuits = CircuitMapping.query.all()
    
    # Create a form instance for CSRF protection
    form = FlaskForm()
    
    return render_template('equipment.html', equipment=equipment, circuits=circuits, form=form)

@app.route('/equipment/add', methods=['POST'])
@login_required
def add_equipment():
    """Add new equipment"""
    name = request.form.get('name')
    ip_address = request.form.get('ip_address')
    ssh_port = request.form.get('ssh_port', 22, type=int)
    username = request.form.get('username')
    password = request.form.get('password')
    
    # Basic validation
    if not all([name, ip_address, username, password]):
        flash('All fields are required', 'danger')
        return redirect(url_for('equipment_list'))
    
    new_equipment = Equipment(
        name=name,
        ip_address=ip_address,
        ssh_port=ssh_port,
        username=username,
        password=password
    )
    
    db.session.add(new_equipment)
    db.session.commit()
    
    flash(f'Equipment "{name}" added successfully', 'success')
    return redirect(url_for('equipment_list'))

@app.route('/equipment/delete/<int:id>', methods=['POST'])
@login_required
def delete_equipment(id):
    """Delete equipment and its circuit mappings"""
    equipment = Equipment.query.get_or_404(id)
    
    # Delete equipment (cascade will delete mappings)
    db.session.delete(equipment)
    db.session.commit()
    
    flash(f'Equipment "{equipment.name}" deleted successfully', 'success')
    return redirect(url_for('equipment_list'))

@app.route('/equipment/edit/<int:id>', methods=['POST'])
@login_required
def edit_equipment(id):
    """Edit equipment"""
    equipment = Equipment.query.get_or_404(id)
    
    equipment.name = request.form.get('name')
    equipment.ip_address = request.form.get('ip_address')
    equipment.ssh_port = request.form.get('ssh_port', 22, type=int)
    equipment.username = request.form.get('username')
    
    # Only update password if a new one is provided
    new_password = request.form.get('password')
    if new_password:
        equipment.password = new_password
    
    db.session.commit()
    
    flash(f'Equipment "{equipment.name}" updated successfully!', 'success')
    return redirect(url_for('equipment_list'))

@app.route('/mapping/add', methods=['POST'])
@login_required
def add_mapping():
    """Add new circuit mapping"""
    circuit_id = request.form.get('circuit_id')
    equipment_id = request.form.get('equipment_id', type=int)
    command = request.form.get('command')
    description = request.form.get('description', '')
    
    # Basic validation
    if not all([circuit_id, equipment_id, command]):
        flash('Circuit ID, equipment and command are required', 'danger')
        return redirect(url_for('equipment_list'))
    
    new_mapping = CircuitMapping(
        circuit_id=circuit_id,
        equipment_id=equipment_id,
        command=command,
        description=description
    )
    
    db.session.add(new_mapping)
    db.session.commit()
    
    flash(f'Circuit mapping for "{circuit_id}" added successfully', 'success')
    return redirect(url_for('equipment_list'))

@app.route('/mapping/delete/<int:id>', methods=['POST'])
@login_required
def delete_mapping(id):
    """Delete circuit mapping"""
    mapping = CircuitMapping.query.get_or_404(id)
    
    db.session.delete(mapping)
    db.session.commit()
    
    flash(f'Circuit mapping deleted successfully', 'success')
    return redirect(url_for('equipment_list'))

@app.route('/mapping/edit/<int:id>', methods=['POST'])
@login_required
def edit_mapping(id):
    """Edit circuit mapping"""
    mapping = CircuitMapping.query.get_or_404(id)
    
    mapping.circuit_id = request.form.get('circuit_id')
    mapping.equipment_id = request.form.get('equipment_id', type=int)
    mapping.command = request.form.get('command')
    mapping.description = request.form.get('description', '')
    
    db.session.commit()
    
    flash('Circuit mapping updated successfully!', 'success')
    return redirect(url_for('equipment_list'))
