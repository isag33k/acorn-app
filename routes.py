import logging
from flask import render_template, request, redirect, url_for, flash, jsonify
from app import app, db
from models import Equipment, CircuitMapping
from utils.ssh_client import SSHClient

logger = logging.getLogger(__name__)

@app.route('/')
def index():
    """Render the main page for alert submission"""
    return render_template('index.html')

@app.route('/submit_alert', methods=['POST'])
def submit_alert():
    """Process the submitted alert and run the SSH command(s)"""
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
            ssh_client = SSHClient(
                hostname=equipment.ip_address,
                port=equipment.ssh_port,
                username=equipment.username,
                password=equipment.password
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
def equipment_list():
    """List all equipment and circuit mappings"""
    equipment = Equipment.query.all()
    circuits = CircuitMapping.query.all()
    return render_template('equipment.html', equipment=equipment, circuits=circuits)

@app.route('/equipment/add', methods=['POST'])
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
def delete_equipment(id):
    """Delete equipment and its circuit mappings"""
    equipment = Equipment.query.get_or_404(id)
    
    # Delete equipment (cascade will delete mappings)
    db.session.delete(equipment)
    db.session.commit()
    
    flash(f'Equipment "{equipment.name}" deleted successfully', 'success')
    return redirect(url_for('equipment_list'))

@app.route('/equipment/edit/<int:id>', methods=['POST'])
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
def delete_mapping(id):
    """Delete circuit mapping"""
    mapping = CircuitMapping.query.get_or_404(id)
    
    db.session.delete(mapping)
    db.session.commit()
    
    flash(f'Circuit mapping deleted successfully', 'success')
    return redirect(url_for('equipment_list'))

@app.route('/mapping/edit/<int:id>', methods=['POST'])
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
