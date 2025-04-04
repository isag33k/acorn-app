from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import datetime

# Available themes
THEMES = {
    'default': 'Default',
    'dark_modern': 'Dark Modern',
    'crystal_green': 'Crystal Green'
}

class User(UserMixin, db.Model):
    """User model for authentication"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_editor = db.Column(db.Boolean, default=False)  # New editor role for circuit editing
    
    # User profile fields
    first_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    avatar = db.Column(db.String(255), nullable=True)  # Store path to avatar image
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # TACACS personal credentials
    tacacs_username = db.Column(db.String(50), nullable=True)
    tacacs_password = db.Column(db.String(100), nullable=True)
    
    # Relationships
    credentials = db.relationship('UserCredential', back_populates='user', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Set the password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if the password matches"""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f"<User {self.username}>"

class UserCredential(db.Model):
    """Model for user-specific credentials for equipment"""
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign key relationship with User
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', back_populates='credentials')
    
    # Foreign key relationship with Equipment
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'), nullable=False)
    equipment = db.relationship('Equipment', back_populates='user_credentials')
    
    # Credentials
    username = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    key_filename = db.Column(db.String(255), nullable=True)  # Path to SSH private key file (optional)
    
    def __repr__(self):
        return f"<UserCredential User:{self.user.username} -> Equip:{self.equipment.name}>"

class Equipment(db.Model):
    """Model for network equipment (routers, switches, etc.)"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    ip_address = db.Column(db.String(15), nullable=False)
    ssh_port = db.Column(db.Integer, default=22)
    username = db.Column(db.String(50), nullable=False)  # Default username (for backward compatibility)
    password = db.Column(db.String(100), nullable=False)  # Default password (for backward compatibility)
    key_filename = db.Column(db.String(255), nullable=True)  # Path to SSH private key file (optional)
    
    # Relationships
    circuit_mappings = db.relationship('CircuitMapping', back_populates='equipment', cascade='all, delete-orphan')
    user_credentials = db.relationship('UserCredential', back_populates='equipment', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Equipment {self.name}>"
    
    def get_credentials_for_user(self, user):
        """Get equipment credentials for a specific user"""
        # Check if this equipment uses TACACS authentication
        if self.username == 'TACACS':
            # First check for equipment-specific TACACS overrides
            user_cred = UserCredential.query.filter_by(user_id=user.id, equipment_id=self.id).first()
            if user_cred:
                return {'username': user_cred.username, 'password': user_cred.password}
                
            # If no equipment-specific credentials, use global TACACS credentials
            if user.tacacs_username and user.tacacs_password:
                return {'username': user.tacacs_username, 'password': user.tacacs_password}
            else:
                # If no personal TACACS credentials are set up, raise an error
                raise ValueError(f"Equipment '{self.name}' requires TACACS credentials but none are set up. Please set up your global TACACS credentials in 'My Credentials' section.")
        
        # For non-TACACS equipment, check if user has specific credentials for this equipment
        user_cred = UserCredential.query.filter_by(user_id=user.id, equipment_id=self.id).first()
        if user_cred:
            creds = {'username': user_cred.username, 'password': user_cred.password}
            if user_cred.key_filename:
                creds['key_filename'] = user_cred.key_filename
            return creds
            
        # Return default credentials if no user-specific credentials found
        creds = {'username': self.username, 'password': self.password}
        if self.key_filename:
            creds['key_filename'] = self.key_filename
        return creds

class CircuitMapping(db.Model):
    """Model for mapping circuit IDs to equipment and commands"""
    id = db.Column(db.Integer, primary_key=True)
    circuit_id = db.Column(db.String(50), nullable=False, index=True)
    
    # Foreign key relationship with Equipment
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'), nullable=False)
    equipment = db.relationship('Equipment', back_populates='circuit_mappings')
    
    # Commands to execute on the equipment (semicolon-separated for multiple commands)
    command = db.Column(db.Text, nullable=False)
    
    # Description of the circuit
    description = db.Column(db.String(255), nullable=True)
    
    # Contact information for the circuit
    contact_name = db.Column(db.String(100), nullable=True)
    contact_email = db.Column(db.String(120), nullable=True)
    contact_phone = db.Column(db.String(20), nullable=True)
    contact_notes = db.Column(db.Text, nullable=True)
    
    def get_commands_list(self):
        """Returns the command string as a list of individual commands"""
        if not self.command:
            return []
        # Split by semicolons but ignore escaped semicolons (\;)
        import re
        # First replace escaped semicolons with a placeholder
        temp = self.command.replace('\\;', '##ESCAPED_SEMICOLON##')
        # Split by actual semicolons
        commands = [cmd.strip() for cmd in temp.split(';')]
        # Restore escaped semicolons
        commands = [cmd.replace('##ESCAPED_SEMICOLON##', ';') for cmd in commands]
        # Return only non-empty commands
        return [cmd for cmd in commands if cmd]
    
    def __repr__(self):
        return f"<CircuitMapping {self.circuit_id} -> {self.equipment.name if self.equipment else 'None'}>"


class Contact(db.Model):
    """Model for global contacts database (POC Database)"""
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False, index=True)
    last_name = db.Column(db.String(50), nullable=False, index=True)
    company = db.Column(db.String(100), nullable=False, index=True)
    email = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(20), nullable=True, index=True)
    mobile = db.Column(db.String(20), nullable=True)
    title = db.Column(db.String(100), nullable=True)
    address = db.Column(db.String(200), nullable=True)
    city = db.Column(db.String(50), nullable=True, index=True)
    state = db.Column(db.String(50), nullable=True, index=True)
    zip_code = db.Column(db.String(20), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    def __repr__(self):
        return f"<Contact {self.first_name} {self.last_name} ({self.company})>"


class AppSettings(db.Model):
    """Model for application settings"""
    id = db.Column(db.Integer, primary_key=True)
    theme = db.Column(db.String(50), nullable=False, default='default')
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    @classmethod
    def get_current_theme(cls):
        """Get the current theme setting"""
        settings = cls.query.first()
        if not settings:
            settings = cls(theme='default')
            db.session.add(settings)
            db.session.commit()
        return settings.theme
    
    @classmethod
    def set_theme(cls, theme_key):
        """Set the active theme"""
        if theme_key not in THEMES:
            raise ValueError(f"Theme '{theme_key}' not found")
            
        settings = cls.query.first()
        if not settings:
            settings = cls(theme=theme_key)
            db.session.add(settings)
        else:
            settings.theme = theme_key
        db.session.commit()
        return settings.theme
    
    def __repr__(self):
        return f"<AppSettings theme={self.theme}>"
