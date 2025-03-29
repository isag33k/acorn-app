# A.C.O.R.N. - Automated Circuit Operations & Reporting Network

A comprehensive web application for automated network circuit monitoring, delivering advanced user management and real-time equipment tracking capabilities.

## Features

- Python Flask-based web application for network circuit monitoring
- SSH-based circuit testing with real network equipment
- User authentication with role-based access control
- Equipment and circuit mapping management
- User-specific SSH credentials management
- Contact information database (POC Database)
- Real SSH server connectivity testing

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

## SSH Server Testing

The application includes a mock SSH server for testing purposes, but it's recommended to connect to real network equipment for production use. The SSH Connection Tester allows you to verify connectivity to any SSH server.

## Security Considerations

- Use HTTPS in production
- Change the default admin password immediately
- Store SSH credentials securely
- Consider using SSH key authentication for production
- Follow best practices for Flask deployments