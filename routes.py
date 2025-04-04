import logging
import datetime
import traceback
import os
import uuid
import json
from flask import render_template, request, redirect, url_for, flash, jsonify, send_from_directory, Response
from flask_login import login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from flask_wtf.csrf import validate_csrf as validate_csrf_token
from wtforms import StringField, PasswordField, BooleanField, SubmitField, EmailField, TextAreaField, SelectField, HiddenField, SearchField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, Optional
from sqlalchemy import or_
from werkzeug.utils import secure_filename
from app import app, db
from models import Equipment, CircuitMapping, User, UserCredential, Contact, AppSettings, THEMES
from utils.ssh_client import SSHClient

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

class SomeClass(FlaskForm):
    # Properly indented class body
    field = StringField('Label', validators=[DataRequired()])
    submit = SubmitField('Submit')


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
    is_editor = BooleanField('Editor Role')
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
    password = PasswordField('Password', validators=[Length(max=100)])
    key_filename = StringField('SSH Private Key File Path', validators=[Length(max=255)])
    submit = SubmitField('Save Credentials')
    
# TACACS credentials form
class TacacsCredentialForm(FlaskForm):
    tacacs_username = StringField('TACACS Username', validators=[DataRequired(), Length(max=50)])
    tacacs_password = PasswordField('TACACS Password', validators=[DataRequired(), Length(max=100)])
    submit = SubmitField('Save TACACS Credentials')
    
# Contact form for POC Database
class ContactForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=50)])
    company = StringField('Company', validators=[DataRequired(), Length(max=100)])
    email = EmailField('Email', validators=[Length(max=120), Email()])
    phone = StringField('Phone', validators=[Length(max=20)])
    mobile = StringField('Mobile', validators=[Length(max=20)])
    title = StringField('Job Title', validators=[Length(max=100)])
    address = StringField('Address', validators=[Length(max=200)])
    city = StringField('City', validators=[Length(max=50)])
    state = StringField('State', validators=[Length(max=50)])
    zip_code = StringField('ZIP/Postal Code', validators=[Length(max=20)])
    notes = TextAreaField('Notes')
    submit = SubmitField('Save Contact')
    
# Contact search form
class ContactSearchForm(FlaskForm):
    search_term = StringField('Search', validators=[Length(max=100)])
    search_field = SelectField('Search By', choices=[
        ('all', 'All Fields'),
        ('name', 'Name (First or Last)'),
        ('company', 'Company'),
        ('phone', 'Phone Number'),
        ('location', 'City/State')
    ])
    submit = SubmitField('Search')
    
# Circuit IDs search form
class CircuitIDSearchForm(FlaskForm):
    search_term = StringField('Search', validators=[Length(max=100)])
    search_field = SelectField('Search By', choices=[
        ('all', 'All Fields'),
        ('circuit_id', 'Circuit ID'),
        ('market', 'Market'),
        ('provider', 'Provider'),
        ('status', 'Status')
    ])
    provider_filter = SelectField('Provider Filter', choices=[
        ('all', 'All Providers')
        # Additional providers will be loaded dynamically
    ])
    status_filter = SelectField('Status Filter', choices=[
        ('all', 'All Statuses'),
        ('ACTIVE', 'ACTIVE'),
        ('INACTIVE', 'INACTIVE'),
        ('PENDING', 'PENDING')
    ])
    submit = SubmitField('Search')
    
# User profile form
class ProfileForm(FlaskForm):
    first_name = StringField('First Name', validators=[Length(max=50)])
    last_name = StringField('Last Name', validators=[Length(max=50)])
    email = EmailField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    phone = StringField('Phone', validators=[Length(max=20)])
    avatar = FileField('Profile Picture', validators=[Optional(), FileAllowed(['jpg', 'png', 'jpeg', 'gif'], 'Images only!')])
    submit = SubmitField('Update Profile')
    
# Password change form
class PasswordChangeForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Change Password')
    
# Theming form for app settings
class ThemingForm(FlaskForm):
    theme = SelectField('Application Theme', validators=[DataRequired()], choices=[])
    submit = SubmitField('Apply Theme')
    
    def __init__(self, *args, **kwargs):
        super(ThemingForm, self).__init__(*args, **kwargs)
        self.theme.choices = [(key, name) for key, name in THEMES.items()]

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

@app.route('/uploads/<path:filename>')
def serve_uploads(filename):
    """Serve files from the uploads directory"""
    # For security, only allow access to avatar files
    if filename.startswith('avatars/'):
        return send_from_directory('uploads', filename)

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
            is_admin=form.is_admin.data,
            is_editor=form.is_editor.data
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
@app.route('/delete_user/<int:id>', methods=['POST'])  # Added for our custom modals
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
        is_editor = 'is_editor' in request.form
        
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
        user.is_editor = is_editor
        
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
    
    # Create a basic form for CSRF token
    form = FlaskForm()
    
    # Create a form for delete operations
    csrf_form = FlaskForm()
    
    # Create a form for TACACS credentials
    tacacs_form = TacacsCredentialForm()
    
    # Check if user has TACACS credentials set
    has_tacacs_credentials = current_user.tacacs_username is not None and current_user.tacacs_password is not None
    
    # Count how many equipment use TACACS authentication (ensure at least 1 for display purposes)
    tacacs_equipment_count = Equipment.query.filter_by(username='TACACS').count()
    
    # Debug info
    for equip in equipment:
        logger.debug(f"Equipment ID: {equip.id}, type: {type(equip.id)}")
    
    logger.debug(f"Credentials dict keys: {list(credentials_dict.keys())}")
    
    return render_template('credentials.html', 
                          equipment=equipment, 
                          credentials=credentials_dict, 
                          form=form, 
                          csrf_form=csrf_form,
                          tacacs_form=tacacs_form,
                          has_tacacs_credentials=has_tacacs_credentials,
                          tacacs_equipment_count=tacacs_equipment_count)

@app.route('/credentials/add', methods=['POST'])
@login_required
def add_credential():
    """Add or update user credential for equipment"""
    try:
        logger.debug(f"Raw POST data: {request.form}")
        csrf_token = request.form.get('csrf_token')
        equipment_id = request.form.get('equipment_id')
        username = request.form.get('username')
        password = request.form.get('password')
        key_filename = request.form.get('key_filename')
        
        logger.debug(f"Extracted values - csrf_token: {csrf_token}, equipment_id: {equipment_id}, username: {username}, password exists: {'yes' if password else 'no'}, key_filename: {key_filename}")
        
        # Basic validation
        if not csrf_token:
            logger.error("Missing CSRF token")
            flash('CSRF token missing', 'danger')
            return redirect(url_for('user_credentials'))
            
        if not equipment_id or not username or (not password and not key_filename):
            missing = []
            if not equipment_id: missing.append("Equipment ID")
            if not username: missing.append("Username") 
            if not password and not key_filename: missing.append("Password or SSH Key file")
            logger.error(f"Missing fields: {missing}")
            flash(f'Missing required fields: {", ".join(missing)}', 'danger')
            return redirect(url_for('user_credentials'))
            
        # Convert equipment_id to integer
        try:
            equipment_id = int(equipment_id)
        except ValueError:
            logger.error(f"Invalid equipment ID: {equipment_id}")
            flash('Invalid equipment ID', 'danger')
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
            credential.key_filename = key_filename
            logger.debug(f"Updated credential for equipment ID {equipment_id}")
            flash('Credential updated successfully', 'success')
        else:
            # Create new
            credential = UserCredential(
                user_id=current_user.id,
                equipment_id=equipment_id,
                username=username,
                password=password,
                key_filename=key_filename
            )
            logger.debug(f"Created new credential for equipment ID {equipment_id}")
            db.session.add(credential)
            flash('Credential added successfully', 'success')
            
        db.session.commit()
    except Exception as e:
        logger.error(f"Error in add_credential: {str(e)}")
        flash(f'An error occurred: {str(e)}', 'danger')
                
    return redirect(url_for('user_credentials'))

@app.route('/credentials/delete/<int:equipment_id>', methods=['POST'])
@login_required
def delete_credential(equipment_id):
    """Delete user credential for equipment"""
    try:
        # Check for CSRF token presence
        csrf_token = request.form.get('csrf_token')
        if not csrf_token:
            logger.error("Missing CSRF token in delete_credential")
            flash('CSRF token missing', 'danger')
            return redirect(url_for('user_credentials'))
            
        # Find the credential
        credential = UserCredential.query.filter_by(
            user_id=current_user.id,
            equipment_id=equipment_id
        ).first_or_404()
        
        logger.debug(f"Deleting credential for equipment ID {equipment_id}")
        db.session.delete(credential)
        db.session.commit()
        flash('Credential deleted successfully', 'success')
        
    except Exception as e:
        logger.error(f"Error in delete_credential: {str(e)}")
        flash(f'An error occurred: {str(e)}', 'danger')
    
    return redirect(url_for('user_credentials'))

@app.route('/credentials/tacacs/add', methods=['POST'])
@login_required
def add_tacacs_credential():
    """Add or update user's global TACACS credentials"""
    try:
        # Check for CSRF token
        form = TacacsCredentialForm()
        if not form.validate_on_submit():
            logger.error("TACACS form validation failed")
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f'{getattr(form, field).label.text}: {error}', 'danger')
            return redirect(url_for('user_credentials'))
        
        # Update user's TACACS credentials
        tacacs_username = form.tacacs_username.data
        tacacs_password = form.tacacs_password.data
        
        # Update the current user
        current_user.tacacs_username = tacacs_username
        current_user.tacacs_password = tacacs_password
        db.session.commit()
        
        logger.debug(f"Updated global TACACS credentials for user {current_user.username}")
        flash('Global TACACS credentials updated successfully', 'success')
        
    except Exception as e:
        logger.error(f"Error in add_tacacs_credential: {str(e)}")
        flash(f'An error occurred: {str(e)}', 'danger')
        db.session.rollback()
    
    return redirect(url_for('user_credentials'))

@app.route('/credentials/tacacs/delete', methods=['POST'])
@login_required
def delete_tacacs_credential():
    """Remove user's global TACACS credentials"""
    try:
        # Check for CSRF token
        form = FlaskForm()
        if not form.validate_on_submit():
            logger.error("CSRF token missing or invalid")
            flash('CSRF token missing or invalid', 'danger')
            return redirect(url_for('user_credentials'))
        
        # Clear the TACACS credentials
        current_user.tacacs_username = None
        current_user.tacacs_password = None
        db.session.commit()
        
        logger.debug(f"Deleted global TACACS credentials for user {current_user.username}")
        flash('Global TACACS credentials removed successfully', 'success')
        
    except Exception as e:
        logger.error(f"Error in delete_tacacs_credential: {str(e)}")
        flash(f'An error occurred: {str(e)}', 'danger')
        db.session.rollback()
    
    return redirect(url_for('user_credentials'))

@app.route('/profile', methods=['GET'])
@login_required
def user_profile():
    """Display and manage user profile"""
    form = ProfileForm()
    
    # Pre-populate form with existing user data
    form.first_name.data = current_user.first_name
    form.last_name.data = current_user.last_name
    form.email.data = current_user.email
    form.phone.data = current_user.phone
    
    return render_template('profile.html', form=form, user=current_user)

@app.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    """Update user profile information"""
    form = ProfileForm()
    
    if form.validate_on_submit():
        try:
            # Update profile fields
            current_user.first_name = form.first_name.data
            current_user.last_name = form.last_name.data
            
            # Check if email already exists (and not the current user's email)
            if form.email.data != current_user.email:
                existing_user = User.query.filter_by(email=form.email.data).first()
                if existing_user and existing_user.id != current_user.id:
                    flash('Email address already in use by another account', 'danger')
                    return redirect(url_for('user_profile'))
                    
            current_user.email = form.email.data
            current_user.phone = form.phone.data
            
            # Handle avatar upload
            if form.avatar.data:
                # Create a unique filename
                filename = secure_filename(form.avatar.data.filename)
                unique_filename = f"{uuid.uuid4().hex}_{filename}"
                
                # Ensure the avatars directory exists (persistent storage)
                avatar_dir = os.path.join('uploads', 'avatars')
                if not os.path.exists(avatar_dir):
                    os.makedirs(avatar_dir, exist_ok=True)
                
                # Save the file to persistent storage
                avatar_path = os.path.join(avatar_dir, unique_filename)
                form.avatar.data.save(avatar_path)
                
                # Delete old avatar if exists (to save space)
                if current_user.avatar:
                    old_avatar_path = current_user.avatar
                    try:
                        if os.path.exists(old_avatar_path):
                            os.remove(old_avatar_path)
                    except Exception as e:
                        logger.warning(f"Error deleting old avatar: {str(e)}")
                
                # Update avatar path in database (store relative path)
                current_user.avatar = avatar_path
            
            # Save changes
            db.session.commit()
            flash('Profile updated successfully', 'success')
            
        except Exception as e:
            logger.error(f"Error updating profile: {str(e)}")
            flash(f'Error updating profile: {str(e)}', 'danger')
            db.session.rollback()
            
    else:
        # Handle validation errors
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{getattr(form, field).label.text}: {error}', 'danger')
                
    return redirect(url_for('user_profile'))

@app.route('/profile/avatar/delete', methods=['POST'])
@login_required
def delete_avatar():
    """Delete the user's profile avatar"""
    try:
        # Check for CSRF token
        form = FlaskForm()
        if not form.validate_on_submit():
            flash('CSRF token missing or invalid', 'danger')
            return redirect(url_for('user_profile'))
            
        # Delete avatar file if exists
        if current_user.avatar:
            try:
                if os.path.exists(current_user.avatar):
                    os.remove(current_user.avatar)
            except Exception as e:
                logger.warning(f"Error deleting avatar file: {str(e)}")
            
        # Clear avatar field in database
        current_user.avatar = None
        db.session.commit()
        flash('Profile picture removed successfully', 'success')
        
    except Exception as e:
        logger.error(f"Error deleting avatar: {str(e)}")
        flash(f'Error removing profile picture: {str(e)}', 'danger')
        db.session.rollback()
        
    return redirect(url_for('user_profile'))

@app.route('/profile/password/change', methods=['POST'])
@login_required
def change_password():
    """Change the user's password"""
    form = PasswordChangeForm()
    
    if form.validate_on_submit():
        try:
            # Verify current password is correct
            if not current_user.check_password(form.current_password.data):
                flash('Current password is incorrect', 'danger')
                return redirect(url_for('user_profile'))
                
            # Set the new password
            current_user.set_password(form.new_password.data)
            db.session.commit()
            
            flash('Password changed successfully', 'success')
            
        except Exception as e:
            logger.error(f"Error changing password: {str(e)}")
            flash(f'Error changing password: {str(e)}', 'danger')
            db.session.rollback()
            
    else:
        # Handle validation errors
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{getattr(form, field).label.text}: {error}', 'danger')
                
    return redirect(url_for('user_profile'))

@app.route('/settings/theme', methods=['GET', 'POST'])
@login_required
def theme_settings():
    """Manage application theme settings (admin only)"""
    if not current_user.is_admin:
        flash('Admin access required', 'danger')
        return redirect(url_for('index'))
        
    form = ThemingForm()
    current_theme = AppSettings.get_current_theme()
    
    # For GET requests, set the form's default value
    if request.method == 'GET':
        form.theme.data = current_theme
    
    if form.validate_on_submit():
        try:
            # Update the theme setting
            theme_key = form.theme.data
            if theme_key in THEMES:
                AppSettings.set_theme(theme_key)
                flash(f'Theme changed to {THEMES[theme_key]}', 'success')
            else:
                flash('Invalid theme selected', 'danger')
        except Exception as e:
            logger.error(f"Error changing theme: {str(e)}")
            flash(f'Error changing theme: {str(e)}', 'danger')
            db.session.rollback()
            
    # Get theme preview images
    theme_previews = {key: url_for('static', filename=f'img/themes/{key}_preview.svg') for key in THEMES.keys()}
    
    return render_template('theme_settings.html', form=form, current_theme=current_theme, 
                           themes=THEMES, theme_previews=theme_previews)

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
    
    # Start timer to measure overall performance
    import time
    start_total_time = time.time()
    
    # Find circuit mappings for the given circuit ID
    mappings = CircuitMapping.query.filter_by(circuit_id=circuit_id).all()
    
    if not mappings:
        flash(f'No equipment mappings found for circuit ID: {circuit_id}', 'warning')
        return redirect(url_for('index'))
    
    # Extract contact information from the first mapping 
    # (assuming the same circuit ID has the same contact across mappings)
    if mappings and (mappings[0].contact_name or mappings[0].contact_email or 
                      mappings[0].contact_phone or mappings[0].contact_notes):
        contact_info = {
            'name': mappings[0].contact_name,
            'email': mappings[0].contact_email,
            'phone': mappings[0].contact_phone,
            'notes': mappings[0].contact_notes
        }
    else:
        contact_info = None
        
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
            
            # Simplified approach (similar to SSH test page)
            for cmd in commands_list:
                # Measure time for this specific command
                start_cmd_time = time.time()
                
                try:
                    # Check if user has TACACS credentials - these are preferred
                    if hasattr(current_user, 'tacacs_username') and current_user.tacacs_username and current_user.tacacs_password:
                        logger.info(f"Using TACACS credentials for user {current_user.username}")
                        username = current_user.tacacs_username
                        password = current_user.tacacs_password
                        # No key file with TACACS
                        ssh_params = {
                            'hostname': equipment.ip_address,
                            'port': equipment.ssh_port,
                            'username': username,
                            'password': password
                        }
                    else:
                        # Use equipment-specific or user-specific credentials
                        logger.info(f"Using equipment-specific credentials for {equipment.name}")
                        ssh_params = {
                            'hostname': equipment.ip_address,
                            'port': equipment.ssh_port,
                            'username': credentials['username'],
                            'password': credentials['password']
                        }
                        
                        # Add key_filename if available in credentials
                        if 'key_filename' in credentials and credentials['key_filename']:
                            ssh_params['key_filename'] = credentials['key_filename']
                            logger.info(f"Using key-based authentication for {equipment.name} with key file: {credentials['key_filename']}")
                    
                    ssh_client = SSHClient(**ssh_params)
                    
                    # Connect to the equipment
                    ssh_client.connect()
                    
                    # Execute command (one at a time)
                    success, output = ssh_client.execute_command(cmd)
                    
                    # Handle extremely large outputs, limit to 200KB instead of 500KB
                    # for faster page rendering
                    if success and isinstance(output, str) and len(output) > 200000:
                        logger.warning(f"Large output ({len(output)} bytes) from {equipment.name}. Truncating for display.")
                        truncated_output = output[:100000] + "\n\n[... Output truncated due to size (showing first 100KB) ...]\n\n" + output[-100000:]
                        output_to_display = truncated_output
                        status = 'success'
                        is_truncated = True
                    else:
                        output_to_display = output
                        status = 'success' if success else 'error'
                        is_truncated = False
                    
                    # Disconnect immediately after command
                    ssh_client.disconnect()
                    
                    # Calculate performance metrics
                    cmd_time = int((time.time() - start_cmd_time) * 1000)  # ms
                    
                    results.append({
                        'equipment_name': equipment.name,
                        'command': cmd,
                        'output': output_to_display,
                        'status': status,
                        'execution_time': cmd_time,
                        'truncated': is_truncated
                    })
                    
                except Exception as inner_e:
                    # Handle command-specific errors
                    logger.error(f"Command error for {equipment.name}, cmd: {cmd}: {str(inner_e)}")
                    results.append({
                        'equipment_name': equipment.name,
                        'command': cmd,
                        'output': f"ERROR: {str(inner_e)}",
                        'status': 'error',
                        'execution_time': int((time.time() - start_cmd_time) * 1000)
                    })
                    
        except ValueError as e:
            # This is specific to the TACACS credential error we're raising in get_credentials_for_user
            error_message = str(e)
            logger.error(f"Credential error for equipment {equipment.name}: {error_message}")
            
            # Add a more user-friendly message for missing credentials
            if "requires TACACS credentials" in error_message:
                results.append({
                    'equipment_name': equipment.name,
                    'command': mapping.command,
                    'output': f"⚠️ TACACS authentication requires global credentials. Please set up your TACACS credentials in 'My Credentials' section.",
                    'status': 'error',
                    'is_tacacs_error': True
                })
            elif "requires personal credentials" in error_message:
                results.append({
                    'equipment_name': equipment.name,
                    'command': mapping.command,
                    'output': f"⚠️ {error_message}",
                    'status': 'error',
                    'is_tacacs_error': True
                })
            else:
                results.append({
                    'equipment_name': equipment.name,
                    'command': mapping.command,
                    'output': error_message,
                    'status': 'error'
                })
                
        except Exception as e:
            logger.error(f"SSH error for equipment {equipment.name}: {str(e)}")
            results.append({
                'equipment_name': equipment.name,
                'command': mapping.command,
                'output': str(e),
                'status': 'error'
            })
    
    # Calculate total execution time
    total_time = int((time.time() - start_total_time) * 1000)
    logger.info(f"Total execution time for circuit {circuit_id}: {total_time}ms")
    
    return render_template('result.html', 
                          circuit_id=circuit_id, 
                          results=results, 
                          contact_info=contact_info,
                          total_time=total_time)

@app.route('/equipment')
@login_required
def equipment_list():
    """List all equipment and circuit mappings"""
    try:
        equipment = Equipment.query.all()
        circuits = CircuitMapping.query.all()
        
        # Create separate form instances for each form on the page
        add_equipment_form = FlaskForm(prefix="add_equipment")
        add_mapping_form = FlaskForm(prefix="add_mapping")
        edit_equipment_form = FlaskForm(prefix="edit_equipment")
        edit_mapping_form = FlaskForm(prefix="edit_mapping")
        delete_form = FlaskForm(prefix="delete")
        
        # For safety, create a regular form instance too
        form = FlaskForm()
        
        app.logger.debug("Equipment list view: Retrieved equipment and circuits, created form instances")
        
        return render_template('equipment.html', 
                            equipment=equipment, 
                            circuits=circuits, 
                            add_equipment_form=add_equipment_form,
                            add_mapping_form=add_mapping_form,
                            edit_equipment_form=edit_equipment_form,
                            edit_mapping_form=edit_mapping_form,
                            delete_form=delete_form,
                            form=form)  # Keep the original form for backward compatibility
    except Exception as e:
        app.logger.error(f"Error in equipment_list route: {str(e)}")
        import traceback
        app.logger.error(traceback.format_exc())
        flash(f"An error occurred: {str(e)}", "danger")
        return redirect(url_for('index'))

@app.route('/equipment/add', methods=['POST'])
@login_required
def add_equipment():
    """Add new equipment"""
    # Simple form validation approach
    form = FlaskForm()
    if not form.validate_on_submit():
        app.logger.error("CSRF validation failed on add equipment form")
        app.logger.error(f"Form data: {request.form}")
        flash('Security validation failed. Please try again.', 'danger')
        return redirect(url_for('equipment_list'))
        
    name = request.form.get('name')
    ip_address = request.form.get('ip_address')
    ssh_port = request.form.get('ssh_port', 22, type=int)
    credential_type = request.form.get('credential_type')
    username = request.form.get('username')
    password = request.form.get('password')
    
    # Basic validation
    if not all([name, ip_address]):
        flash('Equipment name and IP address are required', 'danger')
        return redirect(url_for('equipment_list'))
    
    # Handle key-based authentication
    key_filename = request.form.get('key_filename')
    
    # Handle TACACS credential type
    if credential_type == 'tacacs' or username == 'TACACS':
        username = 'TACACS'
        password = 'TACACS_PLACEHOLDER'  # Will be replaced with user-specific credentials at runtime
        key_filename = None  # No key file for TACACS
    elif not all([username]) or (not password and not key_filename):
        flash('Username and either password or SSH key file are required for custom credentials', 'danger')
        return redirect(url_for('equipment_list'))
    
    # Create equipment with proper key file if provided
    new_equipment = Equipment(
        name=name,
        ip_address=ip_address,
        ssh_port=ssh_port,
        username=username,
        password=password
    )
    
    # Set key filename if provided
    if key_filename and key_filename.strip():
        new_equipment.key_filename = key_filename.strip()
    
    db.session.add(new_equipment)
    db.session.commit()
    
    # If using TACACS, add a reminder to set up personal credentials
    if username == 'TACACS':
        flash(f'Equipment "{name}" added with TACACS authentication. Make sure to set up your personal credentials in the "My Credentials" section.', 'info')
    else:
        flash(f'Equipment "{name}" added successfully with custom credentials', 'success')
    
    return redirect(url_for('equipment_list'))

@app.route('/equipment/delete/<int:id>', methods=['POST'])
@login_required
def delete_equipment(id):
    """Delete equipment and its circuit mappings"""
    # CSRF Validation
    form = FlaskForm()
    if not form.validate_on_submit():
        app.logger.error("CSRF validation failed on delete equipment form")
        flash('Security validation failed. Please try again.', 'danger')
        return redirect(url_for('equipment_list'))
    
    equipment = Equipment.query.get_or_404(id)
    
    # Delete equipment (cascade will delete mappings)
    db.session.delete(equipment)
    db.session.commit()
    
    flash(f'Equipment "{equipment.name}" deleted successfully', 'success')
    return redirect(url_for('equipment_list'))

@app.route('/equipment/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_equipment(id):
    """Edit equipment - now with dedicated page instead of modal"""
    equipment = Equipment.query.get_or_404(id)
    
    # GET request - show the edit form
    if request.method == 'GET':
        return render_template('edit_equipment.html', equipment=equipment)
    
    # POST request - process the form submission
    # CSRF Validation
    form = FlaskForm()
    if not form.validate_on_submit():
        app.logger.error("CSRF validation failed on edit equipment form")
        flash('Security validation failed. Please try again.', 'danger')
        return redirect(url_for('edit_equipment', id=id))
        
    equipment.name = request.form.get('name')
    equipment.ip_address = request.form.get('ip_address')
    equipment.ssh_port = request.form.get('ssh_port', 22, type=int)
    
    credential_type = request.form.get('credential_type')
    username = request.form.get('username')
    
    # Handle TACACS credential type
    if credential_type == 'tacacs' or username == 'TACACS':
        equipment.username = 'TACACS'
        equipment.password = 'TACACS_PLACEHOLDER'  # Will be replaced with user-specific credentials at runtime
        equipment.key_filename = None  # Clear key file when using TACACS
    else:
        # Only update username if not using TACACS
        equipment.username = username
        
        # Only update password if a new one is provided for custom credentials
        new_password = request.form.get('password')
        if new_password:
            equipment.password = new_password
            
        # Update SSH key file path
        key_filename = request.form.get('key_filename')
        if key_filename and key_filename.strip():
            equipment.key_filename = key_filename.strip()
        else:
            equipment.key_filename = None
    
    db.session.commit()
    flash('Equipment updated successfully.', 'success')
    
    # Provide specific feedback based on credential type
    if equipment.username == 'TACACS':
        flash(f'Equipment "{equipment.name}" updated with TACACS authentication. Make sure you have set up your personal credentials in the "My Credentials" section.', 'info')
    else:
        flash(f'Equipment "{equipment.name}" updated successfully with custom credentials!', 'success')
    
    return redirect(url_for('equipment_list'))

@app.route('/mapping/add', methods=['POST'])
@login_required
def add_mapping():
    """Add new circuit mapping"""
    # CSRF Validation
    form = FlaskForm()
    if not form.validate_on_submit():
        app.logger.error("CSRF validation failed on add mapping form")
        flash('Security validation failed. Please try again.', 'danger')
        return redirect(url_for('equipment_list'))
        
    circuit_id = request.form.get('circuit_id')
    equipment_id = request.form.get('equipment_id', type=int)
    command = request.form.get('command')
    description = request.form.get('description', '')
    
    # Contact information
    contact_name = request.form.get('contact_name', '')
    contact_email = request.form.get('contact_email', '')
    contact_phone = request.form.get('contact_phone', '')
    contact_notes = request.form.get('contact_notes', '')
    
    # Basic validation
    if not all([circuit_id, equipment_id, command]):
        flash('Circuit ID, equipment and command are required', 'danger')
        return redirect(url_for('equipment_list'))
    
    new_mapping = CircuitMapping(
        circuit_id=circuit_id,
        equipment_id=equipment_id,
        command=command,
        description=description,
        contact_name=contact_name,
        contact_email=contact_email,
        contact_phone=contact_phone,
        contact_notes=contact_notes
    )
    
    db.session.add(new_mapping)
    db.session.commit()
    
    flash(f'Circuit mapping for "{circuit_id}" added successfully', 'success')
    return redirect(url_for('equipment_list'))

@app.route('/mapping/delete/<int:id>', methods=['POST'])
@login_required
def delete_mapping(id):
    """Delete circuit mapping"""
    # CSRF Validation
    form = FlaskForm()
    if not form.validate_on_submit():
        app.logger.error("CSRF validation failed on delete mapping form")
        flash('Security validation failed. Please try again.', 'danger')
        return redirect(url_for('equipment_list'))
        
    mapping = CircuitMapping.query.get_or_404(id)
    
    db.session.delete(mapping)
    db.session.commit()
    
    flash(f'Circuit mapping deleted successfully', 'success')
    return redirect(url_for('equipment_list'))

@app.route('/mapping/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_mapping(id):
    """Edit circuit mapping on a dedicated page (not a modal)"""
    mapping = CircuitMapping.query.get_or_404(id)
    equipment_list = Equipment.query.all()
    
    # If this is a POST request, process the form data
    if request.method == 'POST':
        # CSRF Validation
        form = FlaskForm()
        if not form.validate_on_submit():
            app.logger.error("CSRF validation failed on edit mapping form")
            flash('Security validation failed. Please try again.', 'danger')
            return redirect(url_for('edit_mapping', id=id))
            
        mapping.circuit_id = request.form.get('circuit_id')
        mapping.equipment_id = request.form.get('equipment_id', type=int)
        mapping.command = request.form.get('command')
        mapping.description = request.form.get('description', '')
        
        # Contact information
        mapping.contact_name = request.form.get('contact_name', '')
        mapping.contact_email = request.form.get('contact_email', '')
        mapping.contact_phone = request.form.get('contact_phone', '')
        mapping.contact_notes = request.form.get('contact_notes', '')
        
        db.session.commit()
        flash('Circuit mapping updated successfully!', 'success')
        return redirect(url_for('equipment_list'))
        
    # If it's a GET request, render the edit form with the mapping data
    form = FlaskForm()  # For CSRF protection
    return render_template('edit_mapping.html', 
                          form=form, 
                          mapping=mapping, 
                          equipment_list=equipment_list)
    
    
# POC Database Routes

@app.route('/contacts', methods=['GET'])
@login_required
def contact_list():
    """Display and search contacts in the POC Database"""
    search_form = ContactSearchForm()
    
    # Get search parameters
    search_term = request.args.get('search_term', '')
    search_field = request.args.get('search_field', 'all')
    
    # Base query
    query = Contact.query
    
    # Apply search filters if a term is provided
    if search_term:
        if search_field == 'name':
            # Search in first_name OR last_name
            query = query.filter(
                or_(
                    Contact.first_name.ilike(f'%{search_term}%'),
                    Contact.last_name.ilike(f'%{search_term}%')
                )
            )
        elif search_field == 'company':
            query = query.filter(Contact.company.ilike(f'%{search_term}%'))
        elif search_field == 'phone':
            query = query.filter(
                or_(
                    Contact.phone.ilike(f'%{search_term}%'),
                    Contact.mobile.ilike(f'%{search_term}%')
                )
            )
        elif search_field == 'location':
            query = query.filter(
                or_(
                    Contact.city.ilike(f'%{search_term}%'),
                    Contact.state.ilike(f'%{search_term}%')
                )
            )
        else:  # 'all' fields
            query = query.filter(
                or_(
                    Contact.first_name.ilike(f'%{search_term}%'),
                    Contact.last_name.ilike(f'%{search_term}%'),
                    Contact.company.ilike(f'%{search_term}%'),
                    Contact.phone.ilike(f'%{search_term}%'),
                    Contact.mobile.ilike(f'%{search_term}%'),
                    Contact.email.ilike(f'%{search_term}%'),
                    Contact.city.ilike(f'%{search_term}%'),
                    Contact.state.ilike(f'%{search_term}%')
                )
            )
    
    # Order by company then last name
    contacts = query.order_by(Contact.company, Contact.last_name).all()
    
    # Create a new contact form
    contact_form = ContactForm()
    
    # CSRF form for delete operations
    csrf_form = FlaskForm()
    
    return render_template(
        'contacts.html',
        contacts=contacts,
        search_form=search_form,
        contact_form=contact_form,
        csrf_form=csrf_form,
        search_term=search_term,
        search_field=search_field
    )



@app.route('/contacts/add', methods=['POST'])
@login_required
def add_contact():
    """Add a new contact to the POC Database"""
    form = ContactForm()
    
    if form.validate_on_submit():
        # Create new contact from form data
        contact = Contact(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            company=form.company.data,
            email=form.email.data,
            phone=form.phone.data,
            mobile=form.mobile.data,
            title=form.title.data,
            address=form.address.data,
            city=form.city.data,
            state=form.state.data,
            zip_code=form.zip_code.data,
            notes=form.notes.data
        )
        
        db.session.add(contact)
        db.session.commit()
        
        flash(f'Contact {contact.first_name} {contact.last_name} added successfully!', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{getattr(form, field).label.text}: {error}', 'danger')
    
    return redirect(url_for('contact_list'))

@app.route('/contacts/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_contact(id):
    """Edit an existing contact"""
    contact = Contact.query.get_or_404(id)
    
    if request.method == 'GET':
        # Pre-populate the form with contact data
        form = ContactForm(obj=contact)
        return render_template('edit_contact.html', form=form, contact=contact)
    
    # POST request - update the contact
    form = ContactForm()
    
    if form.validate_on_submit():
        # Update contact from form data
        contact.first_name = form.first_name.data
        contact.last_name = form.last_name.data
        contact.company = form.company.data
        contact.email = form.email.data
        contact.phone = form.phone.data
        contact.mobile = form.mobile.data
        contact.title = form.title.data
        contact.address = form.address.data
        contact.city = form.city.data
        contact.state = form.state.data
        contact.zip_code = form.zip_code.data
        contact.notes = form.notes.data
        contact.updated_at = datetime.datetime.utcnow()
        
        db.session.commit()
        
        flash(f'Contact {contact.first_name} {contact.last_name} updated successfully!', 'success')
        return redirect(url_for('contact_list'))
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{getattr(form, field).label.text}: {error}', 'danger')
        return redirect(url_for('edit_contact', id=id))

@app.route('/contacts/delete/<int:id>', methods=['POST'])
@login_required
def delete_contact(id):
    """Delete a contact from the POC Database"""
    # Validate CSRF token
    form = FlaskForm()
    if not form.validate_on_submit():
        flash('CSRF token missing or invalid', 'danger')
        return redirect(url_for('contact_list'))
    
    contact = Contact.query.get_or_404(id)
    name = f"{contact.first_name} {contact.last_name}"
    
    db.session.delete(contact)
    db.session.commit()
    
    flash(f'Contact {name} deleted successfully!', 'success')
    return redirect(url_for('contact_list'))

@app.route('/contacts/view/<int:id>')
@login_required
def view_contact(id):
    """View detailed information for a single contact"""
    try:
        contact = Contact.query.get_or_404(id)
        # Create a basic form for CSRF protection
        form = FlaskForm()
        logger.debug(f"Retrieved contact: {contact}")
        logger.debug(f"Contact created_at: {contact.created_at}")
        logger.debug(f"Contact updated_at: {contact.updated_at}")
        return render_template('view_contact.html', contact=contact, form=form)
    except Exception as e:
        logger.error(f"Error in view_contact: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        flash(f"Error viewing contact: {str(e)}", "danger")
        return redirect(url_for('contact_list'))



@app.route('/ssh_test', methods=['GET', 'POST'])
@login_required
def test_ssh_connection():
    """Test SSH connection to a real SSH server"""
    # Create a form for CSRF protection
    form = FlaskForm()
    result = None
    success = None
    connection_time = None
    error = None
    
    # Get parameters from previous form submission if available
    hostname = request.form.get('hostname', '')
    port = request.form.get('port', '22')
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    command = request.form.get('command', 'show version')
    
    if request.method == 'POST' and form.validate_on_submit() and hostname and username and password:
        try:
            # Import the SSH client from utils
            from utils.ssh_client import SSHClient
            import time
            
            # Ensure port is an integer
            try:
                port = int(port)
            except ValueError:
                port = 22
                
            # Measure connection time
            start_time = time.time()
            
            # Connect to the specified SSH server
            # Support both password and key-based authentication
            ssh_params = {
                'hostname': hostname,
                'port': port,
                'username': username,
                'password': password
            }
            
            # Add key file if provided
            key_filename = request.form.get('key_filename')
            if key_filename and key_filename.strip():
                ssh_params['key_filename'] = key_filename.strip()
                logger.info(f"Using key-based authentication with key file: {key_filename}")
                
            ssh_client = SSHClient(**ssh_params)
            
            # Connect
            ssh_client.connect()
            
            # Calculate connection time
            connection_time = int((time.time() - start_time) * 1000)  # Convert to ms
            
            # Execute command
            success, output = ssh_client.execute_command(command)
            
            # Disconnect
            ssh_client.disconnect()
            
            # Set results
            result = output
            # success variable is already set by the execute_command return value
            
        except Exception as e:
            logger.error(f"SSH test error: {str(e)}")
            logger.error(traceback.format_exc())
            
            # More detailed and user-friendly error messages
            error_str = str(e).lower()
            if "authentication failed" in error_str or "auth fail" in error_str:
                error = "Authentication failed. The username or password was rejected by the device."
                result = "CONNECTION ERROR: Authentication failed. Please check your credentials."
            elif "connection refused" in error_str:
                error = f"Connection refused to {hostname}:{port}. The SSH service may not be running or a firewall may be blocking access."
                result = "CONNECTION ERROR: Connection refused. The SSH service may not be running."
            elif "timed out" in error_str:
                error = f"Connection timed out to {hostname}:{port}. The device may be unreachable or network congestion is occurring."
                result = "CONNECTION ERROR: Connection timed out. The device may be unreachable."
            elif "no such file" in error_str and "key_filename" in error_str:
                error = f"SSH key file not found: {request.form.get('key_filename', '')}. Please check the file path."
                result = "KEY ERROR: SSH key file not found. Please check the file path."
            else:
                error = str(e)
                result = f"Failed to execute command: {command}"
            
            success = False
    
    # Pass all form values back to template
    return render_template(
        'ssh_test.html', 
        form=form, 
        result=result, 
        success=success, 
        connection_time=connection_time, 
        error=error,
        hostname=hostname,
        port=port,
        username=username,
        password=password,
        command=command,
        key_filename=request.form.get('key_filename', '')
    )
    
@app.route('/circuit_ids', methods=['GET'])
@login_required
def circuit_ids():
    """Display and search Circuit IDs database"""
    try:
        # Load circuit data from JSON file
        circuit_data_file = 'circuit_ids_data.json'
        if not os.path.exists(circuit_data_file):
            flash('Circuit IDs database file not found', 'danger')
            return render_template('circuit_ids.html', 
                                circuit_data=None, 
                                providers=[], 
                                search_form=CircuitIDSearchForm(),
                                csrf_form=FlaskForm())
        
        with open(circuit_data_file, 'r') as f:
            all_data = json.load(f)
            
        # Check if we're viewing a specific circuit
        circuit_id = request.args.get('circuit_id')
        if circuit_id:
            # Create a back link that preserves the search parameters
            back_params = {}
            for param in ['search_term', 'search_field', 'provider_filter', 'status_filter', 'show_all']:
                value = request.args.get(param)
                if value:
                    back_params[param] = value
            
            back_link = url_for('circuit_ids', **back_params)
            
            # Find the specific circuit
            selected_circuit = None
            for sheet_name, circuits in all_data.items():
                for circuit in circuits:
                    if str(circuit.get('Circuit ID')) == str(circuit_id):
                        # Debug logging for circuit detection
                        logger.debug(f"Found circuit: {circuit.get('Circuit ID')} in {sheet_name}")
                        selected_circuit = circuit
                        break
                if selected_circuit:
                    break
            
            if selected_circuit:
                # Create search form for the filters
                search_form = CircuitIDSearchForm()
                
                # All fields to display (filter out empty and meaningfully organize)
                all_fields = {}
                # Add important fields first in a specific order
                key_order = ['Circuit ID', 'Provider', 'Market', 'Status', 'Description']
                
                # First add the key fields in order
                for key in key_order:
                    if key in selected_circuit and selected_circuit[key] is not None and selected_circuit[key] != '':
                        all_fields[key] = selected_circuit[key]
                
                # Then add all remaining fields except Unnamed
                for key, value in selected_circuit.items():
                    if (key not in all_fields and not key.startswith('Unnamed:') and 
                        value is not None and value != ''):
                        all_fields[key] = value
                
                return render_template('circuit_detail.html',
                                    circuit=selected_circuit,
                                    all_fields=all_fields,
                                    back_link=back_link,
                                    search_form=search_form,
                                    csrf_form=FlaskForm())
            else:
                flash(f'Circuit ID "{circuit_id}" not found.', 'warning')
                # Redirect back to search page without the circuit_id parameter
                redirect_params = {k: v for k, v in request.args.items() if k != 'circuit_id'}
                return redirect(url_for('circuit_ids', **redirect_params))
        
        # Get search parameters
        search_term = request.args.get('search_term', '')
        search_field = request.args.get('search_field', 'all')
        provider_filter = request.args.get('provider_filter', 'all')
        status_filter = request.args.get('status_filter', 'ACTIVE')
        show_all = request.args.get('show_all', '0') == '1'  # Show all records if show_all=1
        
        # Process data from all sheets and combine into a single list for display
        all_circuits = []
        
        # Define valid providers (only these will be shown in filter dropdown)
        valid_providers = ['Arelion', 'Accelecom', 'Cogent', 'Cologix - Jacksonville', 
                          'CoreSite - Atlanta', 'Lumen', 'Seimitsu', 'Uniti', 
                          'CenturyLink', 'Windstream']
        
        providers = set(['all'])  # For filter dropdown, starting with 'all'
        for provider in valid_providers:
            providers.add(provider)
            
        # Set fixed status options - only these three values will be shown in dropdown regardless of data
        statuses = set(['all', 'ACTIVE', 'INACTIVE', 'PENDING'])
        
        # Key fields to include
        key_fields = ['Market', 'Provider', 'Circuit ID', 'Status', 'Description', 
                      'Parent CID', 'Access CID', 'Access Provider']
        
        # Process each sheet
        for sheet_name, circuits in all_data.items():
            for circuit in circuits:
                # Skip rows without a circuit ID or description, or that are header-like rows
                if not circuit.get('Circuit ID') and not circuit.get('Description'):
                    continue
                    
                # Skip if we have header-like rows (Market, Arelion, Circuit ID, etc.)
                market = str(circuit.get('Market', '')).lower()
                provider = str(circuit.get('Provider', '')).lower() 
                circuit_id = str(circuit.get('Circuit ID', '')).lower()
                description = str(circuit.get('Description', '')).lower()
                status = str(circuit.get('Status', '')).lower()
                
                # Check for header-like pattern with field names as values
                # For this logic, we consider it to be a header row if:
                # 1. At least one field is a field name (e.g., "Market", "Circuit ID", etc.)
                # 2. No field contains any actual useful data (only contains field names or provider names or is empty)
                
                # These are descriptive field headers, not actual circuit data
                # Make sure to include both capitalized and lowercase versions
                forbidden_values = [
                    'data center id', 'Data Center ID', 
                    'cage id', 'Cage ID',
                    'cabinet number', 'Cabinet Number',
                    'patch panel id', 'Patch Panel ID',
                    'patch panel port capacity', 'Patch Panel Port Capacity',
                    'patch panel ports used', 'Patch Panel Ports Used',
                    'patch panel ports available', 'Patch Panel Ports Available',
                    'patch panel connector type', 'Patch Panel Connector Type',
                    'data center description', 'Data Center Description',
                    '-', 'patch panel connector', 'Patch Panel Connector'
                ]
                
                # Check for header rows - these can appear in various patterns:
                # 1. Market field contains a forbidden value (e.g., "Data Center ID")
                # 2. Market is empty but Circuit ID contains a forbidden value
                # 3. Market is "-" (a dash or hyphen) - often used as spacers
                
                # Filter out any row where Market field contains any of our forbidden values
                if 'Market' in circuit and circuit['Market'] and isinstance(circuit['Market'], str):
                    market_value = circuit['Market']
                    
                    # Check for exact match with forbidden values
                    if market_value in forbidden_values:
                        logger.debug(f"Filtering out forbidden header in Market: {market_value} from {sheet_name}")
                        continue
                        
                    # Check lowercase match
                    if market_value.lower() in [val.lower() for val in forbidden_values]:
                        logger.debug(f"Filtering out forbidden header (case-insensitive) in Market: {market_value} from {sheet_name}")
                        continue
                        
                    # Check for other problematic Market values
                    if market_value == "-" or market_value == "":
                        logger.debug(f"Filtering out empty or dash Market value: '{market_value}' from {sheet_name}")
                        continue
                
                # Also filter rows where Circuit ID field contains forbidden values 
                if 'Circuit ID' in circuit and circuit['Circuit ID'] and isinstance(circuit['Circuit ID'], str):
                    circuit_id_value = circuit['Circuit ID']
                    
                    # Check for exact match with forbidden values
                    if circuit_id_value in forbidden_values:
                        logger.debug(f"Filtering out forbidden header in Circuit ID: {circuit_id_value} from {sheet_name}")
                        continue
                        
                    # Check lowercase match
                    if circuit_id_value.lower() in [val.lower() for val in forbidden_values]:
                        logger.debug(f"Filtering out forbidden header (case-insensitive) in Circuit ID: {circuit_id_value} from {sheet_name}")
                        continue
                
                # Special case for rows where circuit_id = provider = "Cologix - Jacksonville"
                # This pattern appears in the problematic rows from the screenshot
                if (circuit.get('Circuit ID') == 'Cologix - Jacksonville' and 
                    circuit.get('Provider') == 'Cologix - Jacksonville' and
                    circuit.get('Status') == 'ACTIVE' and
                    (not circuit.get('Description') or circuit.get('Description') == '-')):
                    logger.debug(f"Filtering out Cologix - Jacksonville entry with empty/missing Description")
                    continue
                
                # Filter out entries where Market = "Market" and Circuit ID = "Circuit ID"
                # This catches header rows that made it into the data
                if ('Market' in circuit and 'Circuit ID' in circuit and
                    circuit.get('Market') == 'Market' and 
                    circuit.get('Circuit ID') == 'Circuit ID'):
                    logger.debug(f"Filtering out header row with Market='Market' and Circuit ID='Circuit ID' from {sheet_name}")
                    continue
                    
                # Filter out entries where Provider field = Provider name (e.g., "Uniti", "Windstream") 
                # and Circuit ID = "Circuit ID" (based on screenshot example)
                if ('Provider' in circuit and 'Circuit ID' in circuit and
                    circuit.get('Circuit ID') == 'Circuit ID' and
                    circuit.get('Provider') in ['Uniti', 'Windstream']):
                    logger.debug(f"Filtering out header row with Provider={circuit.get('Provider')} and Circuit ID='Circuit ID' from {sheet_name}")
                    continue
                
                # Extra check for the "Market" rows with Uniti or Windstream from the screenshot
                if ('Market' in circuit and 'Provider' in circuit and 'Circuit ID' in circuit and
                    circuit.get('Market') == 'Market' and 
                    circuit.get('Provider') in ['Uniti', 'Windstream'] and
                    circuit.get('Circuit ID') == 'Circuit ID'):
                    logger.debug(f"Filtering out Market='Market' row with Provider={circuit.get('Provider')} from {sheet_name}")
                    continue
                
                # Special case shown in the screenshot where Market is literally "Market" and Provider is Uniti or Windstream
                if ('Market' in circuit and 'Provider' in circuit and
                    circuit.get('Market') == 'Market' and 
                    circuit.get('Provider') in ['Uniti', 'Windstream']):
                    logger.debug(f"Filtering out row with Market='Market' and Provider={circuit.get('Provider')} from {sheet_name}")
                    continue
                
                # Count how many fields contain only field names or provider names
                header_field_count = 0
                total_fields_with_data = 0
                
                for field in key_fields:
                    field_value = str(circuit.get(field, '')).lower()
                    if field_value:
                        total_fields_with_data += 1
                        
                        # Check if this field contains its own name
                        if field_value == field.lower():
                            header_field_count += 1
                        # Check for provider names as values
                        elif field_value in ['accelecom', 'arelion', 'cogent']:
                            header_field_count += 1
                
                # If any field is a header name AND all populated fields are header-like, skip it
                if header_field_count > 0 and header_field_count == total_fields_with_data:
                    continue
                
                # We're using a predefined provider list, so don't collect from data
                # Just update the circuit provider if needed
                if circuit.get('Provider') and circuit.get('Provider') not in valid_providers:
                    circuit['Provider'] = sheet_name
                
                # No longer adding statuses from data - using only our predefined list
                # of ACTIVE, INACTIVE, and PENDING
                
                # Even with show_all, we still want to skip rows that are just 
                # field name matches (e.g., Market = Market, Provider = Provider, etc.)
                # or header-like rows (Market, Arelion, Circuit ID, etc.)
                if show_all:
                    # Check for specific unwanted patterns:
                    # 1. Circuit ID field contains a forbidden value (e.g., "Data Center ID", "Cage ID")
                    # 2. Any field equals its own field name
                    # 3. Header-like rows with just field names
                    
                    # Skip if the circuit has any key field that equals its field name
                    skip_circuit = False
                    
                    # Case 1: Check all key fields for forbidden values (Data Center ID, Cage ID, etc.)
                    # First check Market, Circuit ID, and Description fields
                    for field in ['Market', 'Circuit ID', 'Description']:
                        if field in circuit and circuit[field] and isinstance(circuit[field], str):
                            field_value = circuit[field]
                            # Check exact match
                            if field_value in forbidden_values:
                                logger.debug(f"Filtering out forbidden header in {field} (exact match) in show_all: {field_value} from {sheet_name}")
                                skip_circuit = True
                                break
                            # Check lowercase match
                            if field_value.lower() in [val.lower() for val in forbidden_values]:
                                logger.debug(f"Filtering out forbidden header in {field} (case-insensitive) in show_all: {field_value} from {sheet_name}")
                                skip_circuit = True
                                break
                    
                    # Special case for rows where circuit_id = provider = "Cologix - Jacksonville"
                    # This pattern appears in the problematic rows from the screenshot
                    if not skip_circuit and (circuit.get('Circuit ID') == 'Cologix - Jacksonville' and 
                        circuit.get('Provider') == 'Cologix - Jacksonville' and
                        circuit.get('Status') == 'ACTIVE' and
                        (not circuit.get('Description') or circuit.get('Description') == '-')):
                        logger.debug(f"Filtering out Cologix - Jacksonville entry with empty/missing Description in show_all")
                        skip_circuit = True
                     
                    # Filter out entries where Market = "Market" and Circuit ID = "Circuit ID"
                    # This catches header rows that made it into the data
                    if not skip_circuit and ('Market' in circuit and 'Circuit ID' in circuit and
                        circuit.get('Market') == 'Market' and 
                        circuit.get('Circuit ID') == 'Circuit ID'):
                        logger.debug(f"Filtering out header row with Market='Market' and Circuit ID='Circuit ID' from {sheet_name} in show_all")
                        skip_circuit = True
                        
                    # Filter out entries where Provider field = Provider name (e.g., "Uniti", "Windstream") 
                    # and Circuit ID = "Circuit ID" (based on screenshot example)
                    if not skip_circuit and ('Provider' in circuit and 'Circuit ID' in circuit and
                        circuit.get('Circuit ID') == 'Circuit ID' and
                        circuit.get('Provider') in ['Uniti', 'Windstream']):
                        logger.debug(f"Filtering out header row with Provider={circuit.get('Provider')} and Circuit ID='Circuit ID' from {sheet_name} in show_all")
                        skip_circuit = True
                    
                    # Extra check for the "Market" rows with Uniti or Windstream from the screenshot
                    if not skip_circuit and ('Market' in circuit and 'Provider' in circuit and 'Circuit ID' in circuit and
                        circuit.get('Market') == 'Market' and 
                        circuit.get('Provider') in ['Uniti', 'Windstream'] and
                        circuit.get('Circuit ID') == 'Circuit ID'):
                        logger.debug(f"Filtering out Market='Market' row with Provider={circuit.get('Provider')} from {sheet_name} in show_all")
                        skip_circuit = True
                        
                    # Special case shown in the screenshot where Market is literally "Market" and Provider is Uniti or Windstream
                    if not skip_circuit and ('Market' in circuit and 'Provider' in circuit and
                        circuit.get('Market') == 'Market' and 
                        circuit.get('Provider') in ['Uniti', 'Windstream']):
                        logger.debug(f"Filtering out row with Market='Market' and Provider={circuit.get('Provider')} from {sheet_name} in show_all")
                        skip_circuit = True
                    
                    # Case 2: Check if any field equals its own name
                    if not skip_circuit:
                        for field in key_fields:
                            field_value = str(circuit.get(field, '')).lower()
                            if field_value and field_value == field.lower():
                                skip_circuit = True
                                break
                    
                    # Case 3: Check for header-like rows with key field names as values
                    if not skip_circuit:
                        # Count how many fields contain only field names or provider names
                        header_field_count = 0
                        total_fields_with_data = 0
                        
                        for field in key_fields:
                            field_value = str(circuit.get(field, '')).lower()
                            if field_value:
                                total_fields_with_data += 1
                                
                                # Check if this field contains its own name
                                if field_value == field.lower():
                                    header_field_count += 1
                                # Check for provider names as values
                                elif field_value in ['accelecom', 'arelion', 'cogent']:
                                    header_field_count += 1
                        
                        # If any field is a header name AND all populated fields are header-like, skip it
                        if header_field_count > 0 and header_field_count == total_fields_with_data:
                            skip_circuit = True
                    
                    if skip_circuit:
                        continue
                        
                    # Include the circuit if it passed the field name check
                    all_circuits.append(circuit)
                    continue
                
                # Apply provider filter if selected
                if provider_filter != 'all' and circuit.get('Provider') != provider_filter:
                    continue
                
                # Apply status filter if selected
                if status_filter != 'all' and circuit.get('Status') != status_filter:
                    continue
                
                # Apply search filter if search term is provided
                if search_term:
                    # Handle case where circuit ID might be in different formats (with or without dashes)
                    # Remove non-alphanumeric chars for more flexible matching
                    if search_field == 'circuit_id':
                        # Skip if search term is exactly "Circuit ID"
                        if search_term.lower() == "circuit id":
                            continue
                            
                        circuit_id = str(circuit.get('Circuit ID') or '').lower()
                        search = search_term.lower()
                        
                        # Try exact match first
                        if search in circuit_id:
                            all_circuits.append(circuit)
                            continue
                        
                        # Try normalized match (remove non-alphanumeric characters)
                        circuit_id_norm = ''.join(c for c in circuit_id if c.isalnum())
                        search_norm = ''.join(c for c in search if c.isalnum())
                        
                        if search_norm and circuit_id_norm and search_norm in circuit_id_norm:
                            all_circuits.append(circuit)
                            continue
                        else:
                            continue  # Skip if no match
                            
                    elif search_field == 'market':
                        # Skip if search term is exactly "Market"
                        if search_term.lower() == "market":
                            continue
                        if not circuit.get('Market') or search_term.lower() not in str(circuit.get('Market')).lower():
                            continue
                    elif search_field == 'provider':
                        # Skip if search term is exactly "Provider"
                        if search_term.lower() == "provider":
                            continue
                        if not circuit.get('Provider') or search_term.lower() not in str(circuit.get('Provider')).lower():
                            continue
                    elif search_field == 'status':
                        # Skip if search term is exactly "Status"
                        if search_term.lower() == "status":
                            continue
                        if not circuit.get('Status') or search_term.lower() not in str(circuit.get('Status')).lower():
                            continue
                    else:  # 'all' fields
                        # Search across multiple fields
                        found = False
                        for field in key_fields:
                            # Skip if the search term is exactly a field name (case-insensitive)
                            if search_term.lower() == field.lower():
                                continue
                                
                            # Check if the field value contains the search term
                            if field in circuit and circuit[field] and search_term.lower() in str(circuit[field]).lower():
                                found = True
                                break
                                
                        # Try normalized circuit ID match as well
                        if not found and 'Circuit ID' in circuit and circuit['Circuit ID']:
                            circuit_id = str(circuit.get('Circuit ID')).lower()
                            search = search_term.lower()
                            circuit_id_norm = ''.join(c for c in circuit_id if c.isalnum())
                            search_norm = ''.join(c for c in search if c.isalnum())
                            
                            if search_norm and circuit_id_norm and search_norm in circuit_id_norm:
                                found = True
                                
                        if not found:
                            continue
                
                # Circuit passed all filters, include in results
                all_circuits.append(circuit)
        
        # Sort by Provider, then Circuit ID - convert values to strings to avoid type comparison issues
        all_circuits.sort(key=lambda x: (str(x.get('Provider', '')), str(x.get('Circuit ID', ''))))
        
        # Create search form
        search_form = CircuitIDSearchForm()
        
        # Update the providers choices in the form
        provider_choices = [('all', 'All Providers')]
        for provider in sorted(providers):
            if provider != 'all':
                provider_choices.append((provider, provider))
        search_form.provider_filter.choices = provider_choices
        
        # Set the status choices in the form to only the three allowed values
        status_choices = [
            ('all', 'All Statuses'),
            ('ACTIVE', 'ACTIVE'),
            ('INACTIVE', 'INACTIVE'),
            ('PENDING', 'PENDING')
        ]
        search_form.status_filter.choices = status_choices
        
        # CSRF form for any actions that require it
        csrf_form = FlaskForm()
        
        return render_template('circuit_ids.html', 
                              circuit_data=all_circuits, 
                              search_form=search_form,
                              csrf_form=csrf_form,
                              search_term=search_term,
                              search_field=search_field,
                              provider_filter=provider_filter,
                              status_filter=status_filter,
                              count=len(all_circuits),
                              key_fields=key_fields)
    
    except Exception as e:
        logger.error(f"Error loading circuit IDs: {str(e)}")
        logger.error(traceback.format_exc())
        flash(f'Error loading Circuit IDs data: {str(e)}', 'danger')
        return render_template('circuit_ids.html', 
                              circuit_data=None, 
                              search_form=CircuitIDSearchForm(),
                              csrf_form=FlaskForm())
                              
@app.route('/update_circuit', methods=['POST'])
@login_required
def update_circuit():
    """Update circuit information in the JSON database"""
    # Check if user has editor or admin privileges
    if not current_user.is_admin and not current_user.is_editor:
        flash('You do not have permission to edit circuits', 'danger')
        return redirect(url_for('circuit_ids'))
        
    # CSRF Validation
    form = FlaskForm()
    if not form.validate_on_submit():
        flash('Security validation failed. Please try again.', 'danger')
        return redirect(url_for('circuit_ids'))
    
    # Get form data
    original_circuit_id = request.form.get('original_circuit_id')
    provider = request.form.get('provider')
    circuit_id = request.form.get('circuit_id')
    status = request.form.get('status')
    market = request.form.get('market')
    description = request.form.get('description')
    parent_cid = request.form.get('parent_cid')
    access_cid = request.form.get('access_cid')
    access_provider = request.form.get('access_provider')
    capacity = request.form.get('capacity')
    
    if not original_circuit_id or not provider:
        flash('Missing required fields', 'danger')
        return redirect(url_for('circuit_ids'))
    
    try:
        # Load circuit data
        circuit_data_file = 'circuit_ids_data.json'
        if not os.path.exists(circuit_data_file):
            flash('Circuit IDs database file not found', 'danger')
            return redirect(url_for('circuit_ids'))
            
        with open(circuit_data_file, 'r') as f:
            all_data = json.load(f)
        
        # Find and update the circuit
        found = False
        for sheet_name, circuits in all_data.items():
            for i, circuit in enumerate(circuits):
                if str(circuit.get('Circuit ID')) == str(original_circuit_id) and str(circuit.get('Provider')) == str(provider):
                    # Update the circuit with new values
                    all_data[sheet_name][i]['Circuit ID'] = circuit_id
                    all_data[sheet_name][i]['Status'] = status
                    
                    if market:
                        all_data[sheet_name][i]['Market'] = market
                    if description:
                        all_data[sheet_name][i]['Description'] = description
                    if parent_cid:
                        all_data[sheet_name][i]['Parent CID'] = parent_cid
                    if access_cid:
                        all_data[sheet_name][i]['Access CID'] = access_cid
                    if access_provider:
                        all_data[sheet_name][i]['Access Provider'] = access_provider
                    if capacity:
                        all_data[sheet_name][i]['Capacity'] = capacity
                    
                    found = True
                    break
            if found:
                break
        
        if not found:
            flash(f'Circuit ID "{original_circuit_id}" not found', 'warning')
            return redirect(url_for('circuit_ids'))
        
        # Save updated data back to file
        with open(circuit_data_file, 'w') as f:
            json.dump(all_data, f, indent=4)
        
        flash(f'Circuit "{original_circuit_id}" updated successfully', 'success')
        
        # Redirect to view the updated circuit
        if original_circuit_id != circuit_id:
            # If the circuit ID changed, redirect to the new one
            return redirect(url_for('circuit_ids', circuit_id=circuit_id))
        else:
            # Otherwise redirect to the same circuit to see changes
            return redirect(url_for('circuit_ids', circuit_id=original_circuit_id))
            
    except Exception as e:
        logger.error(f"Error updating circuit: {str(e)}")
        logger.error(traceback.format_exc())
        flash(f'Error updating circuit: {str(e)}', 'danger')
        return redirect(url_for('circuit_ids', circuit_id=original_circuit_id))

@app.route('/delete_circuit', methods=['POST'])
@login_required
def delete_circuit():
    """Delete circuit from the JSON database"""
    # Check if user has editor or admin privileges
    if not current_user.is_admin and not current_user.is_editor:
        flash('You do not have permission to delete circuits', 'danger')
        return redirect(url_for('circuit_ids'))
        
    # CSRF Validation
    form = FlaskForm()
    if not form.validate_on_submit():
        flash('Security validation failed. Please try again.', 'danger')
        return redirect(url_for('circuit_ids'))
    
    # Get form data
    circuit_id = request.form.get('circuit_id')
    provider = request.form.get('provider')
    
    if not circuit_id or not provider:
        flash('Missing required fields', 'danger')
        return redirect(url_for('circuit_ids'))
    
    try:
        # Load circuit data
        circuit_data_file = 'circuit_ids_data.json'
        if not os.path.exists(circuit_data_file):
            flash('Circuit IDs database file not found', 'danger')
            return redirect(url_for('circuit_ids'))
            
        with open(circuit_data_file, 'r') as f:
            all_data = json.load(f)
        
        # Find and delete the circuit
        found = False
        for sheet_name, circuits in all_data.items():
            for i, circuit in enumerate(circuits):
                if str(circuit.get('Circuit ID')) == str(circuit_id) and str(circuit.get('Provider')) == str(provider):
                    # Remove the circuit from the list
                    deleted_circuit = all_data[sheet_name].pop(i)
                    logger.info(f"Deleted circuit: {deleted_circuit}")
                    found = True
                    break
            if found:
                break
        
        if not found:
            flash(f'Circuit ID "{circuit_id}" not found', 'warning')
            return redirect(url_for('circuit_ids'))
        
        # Save updated data back to file
        with open(circuit_data_file, 'w') as f:
            json.dump(all_data, f, indent=4)
        
        flash(f'Circuit "{circuit_id}" deleted successfully', 'success')
        return redirect(url_for('circuit_ids'))
            
    except Exception as e:
        logger.error(f"Error deleting circuit: {str(e)}")
        logger.error(traceback.format_exc())
        flash(f'Error deleting circuit: {str(e)}', 'danger')
        return redirect(url_for('circuit_ids'))
