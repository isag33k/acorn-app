# A.C.O.R.N. - Automated Circuit Operations & Reporting Network

A comprehensive web application for automated network circuit monitoring, delivering advanced SSH connection management and real-time equipment tracking capabilities.

## Features

- Python Flask-based web application for network circuit monitoring
- SSH-based circuit testing with real network equipment
- User authentication with role-based access control
- Equipment and circuit mapping management
- User-specific SSH credentials management
- Contact information database (POC Database)
- Circuit ID Database with provider-specific information
- Real SSH server connectivity testing
- Customizable UI theme system

## Technical Stack

- **Backend**: Python Flask with SQLAlchemy ORM
- **Database**: PostgreSQL
- **Authentication**: Flask-Login with password hashing
- **SSH Connectivity**: Paramiko SSH library
- **Frontend**: Bootstrap 5 with dark theme
- **Icons**: Font Awesome
- **Deployment**: Gunicorn WSGI server

## Deployment Instructions

### Prerequisites

- Python 3.11 or newer
- PostgreSQL database
- Network equipment with SSH access

### Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd acorn
   ```

2. **Set up environment variables** (create a `.env` file):
   ```
   FLASK_SECRET_KEY=your_secret_key_here
   DATABASE_URL=postgresql://username:password@hostname/database
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize the database**:
   ```bash
   python -c "from app import app, db; app.app_context().push(); db.create_all()"
   ```

5. **Create an initial admin user**:
   ```bash
   python setup_test_environment.py
   ```

6. **Start the application**:
   ```bash
   gunicorn --bind 0.0.0.0:5000 main:app
   ```

## Usage

1. Log in with the default admin credentials (username: `admin`, password: `Welcome1@123`)
2. Add your network equipment under the "Manage Equipment" section
3. Add circuit mappings to connect circuit IDs with equipment and commands
4. Test SSH connectivity using the "SSH Connection Tester" tool
5. Enter circuit IDs on the main page to check their status
6. Use the Circuit ID Database to search and filter circuit information by provider
7. View detailed circuit information by clicking on any circuit in the database
8. Adjust the application theme through the admin settings

## Circuit ID Database

The Circuit ID Database provides a comprehensive view of all circuit information across different providers. Key features include:

- Searching and filtering circuits by provider, status, and circuit ID
- Detailed view of individual circuit information
- Provider-specific status handling (e.g., Cologix - Jacksonville status is ACTIVE when End Date is empty)
- Unique circuit ID generation for records with duplicate IDs
- Data is sourced from Excel files and processed using pandas

## Data Processing

The application includes several utilities for processing circuit data:

- `read_excel.py`: Reads Excel files and converts them to JSON format
- `analyze_excel.py`: Analyzes Excel file structure to identify column mappings
- `fix_duplicate_circuit_ids.py`: Fixes duplicate circuit IDs by assigning unique identifiers
- `restore_other_statuses.py`: Ensures proper status values for all provider circuits
- `update_cologix_status.py`: Updates Cologix circuit statuses based on End Date

## SSH Server Testing

The application includes a mock SSH server for testing purposes, but it's recommended to connect to real network equipment for production use. The SSH Connection Tester allows you to verify connectivity to any SSH server.

## Security Considerations

- Use HTTPS in production
- Change the default admin password immediately
- Store SSH credentials securely
- Consider using SSH key authentication for production
- Follow best practices for Flask deployments