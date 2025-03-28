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
    
    # Command to execute on the equipment
    command = db.Column(db.String(255), nullable=False)
    
    # Description of the circuit
    description = db.Column(db.String(255), nullable=True)
    
    def __repr__(self):
        return f"<CircuitMapping {self.circuit_id} -> {self.equipment.name if self.equipment else 'None'}>"
