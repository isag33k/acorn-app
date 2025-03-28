from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    """User model for authentication"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    
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
    
    # Relationships
    circuit_mappings = db.relationship('CircuitMapping', back_populates='equipment', cascade='all, delete-orphan')
    user_credentials = db.relationship('UserCredential', back_populates='equipment', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Equipment {self.name}>"
    
    def get_credentials_for_user(self, user):
        """Get equipment credentials for a specific user"""
        # Check if user has specific credentials for this equipment
        user_cred = UserCredential.query.filter_by(user_id=user.id, equipment_id=self.id).first()
        if user_cred:
            return {'username': user_cred.username, 'password': user_cred.password}
        # Return default credentials if no user-specific credentials found
        return {'username': self.username, 'password': self.password}

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
