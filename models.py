from app import db

class Equipment(db.Model):
    """Model for network equipment (routers, switches, etc.)"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    ip_address = db.Column(db.String(15), nullable=False)
    ssh_port = db.Column(db.Integer, default=22)
    username = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    
    # Relationships
    circuit_mappings = db.relationship('CircuitMapping', back_populates='equipment', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Equipment {self.name}>"

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
