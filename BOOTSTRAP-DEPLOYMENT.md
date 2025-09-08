# SSLH LabHub Bootstrap Deployment

## 🚀 Quick Start

Deploy the entire SSLH LabHub spikesorting system with a single command:

```bash
./bootstrap-deploy.sh local
```

## 📋 Features

- **One-Command Deployment**: Complete system setup with dependencies, database, and workers
- **Environment-Specific Configuration**: Local development, production, or worker-only deployments
- **Automatic Service Management**: Starts Django server and workers with proper configuration
- **Clean Shutdown**: Graceful service stopping with Ctrl+C
- **Status Monitoring**: Built-in service status checking
- **SSL Support**: Optional HTTPS deployment with self-signed certificates

## 🎯 Usage Examples

### Local Development
```bash
# Basic local deployment
./bootstrap-deploy.sh local

# Local deployment on custom port
./bootstrap-deploy.sh local --port 9000

# Skip database migrations
./bootstrap-deploy.sh local --no-migrate
```

### Production Deployment
```bash
# Production with SSL
./bootstrap-deploy.sh production --ssl --workers 4

# Production on custom port
./bootstrap-deploy.sh production --port 8443 --workers 2
```

### Worker-Only Deployment
```bash
# Just start workers (no Django server)
./bootstrap-deploy.sh worker-only
```

### Service Management
```bash
# Check service status
./bootstrap-deploy.sh status

# Stop all services
./bootstrap-deploy.sh stop

# Restart services
./bootstrap-deploy.sh restart
```

## 📖 Complete Command Reference

### Environments
- `local` - Local development setup (default)
- `production` - Production deployment with Gunicorn
- `worker-only` - Worker-only deployment (no Django server)

### Options
- `--port PORT` - Server port (default: 8000 for local, 8443 for production)
- `--ssl` - Enable SSL/HTTPS with self-signed certificates
- `--no-migrate` - Skip database migrations
- `--no-collectstatic` - Skip static file collection
- `--workers N` - Number of Gunicorn worker processes (default: 2)
- `--help` - Show help message

## 🌐 Deployed Services

After successful deployment, access these URLs:

### Web Interface
- **Job Submission**: `http://127.0.0.1:8000/qmodel/submit/`
- **Job List**: `http://127.0.0.1:8000/qmodel/jobs/`

### API Endpoints
- **Next Job**: `http://127.0.0.1:8000/qmodel/next-job/`
- **Job Status**: `http://127.0.0.1:8000/qmodel/status/{job_id}/`

## 🔧 What the Bootstrap Script Does

1. **System Verification**: Checks Python 3.11+, pip, and other requirements
2. **Virtual Environment**: Creates and activates Python virtual environment
3. **Dependencies**: Installs all required packages from `requirements.txt`
4. **Database Setup**: Runs Django migrations and sets up SQLite database
5. **Static Files**: Collects Django static files
6. **SSL Certificates**: Generates self-signed certificates (if --ssl enabled)
7. **Directory Creation**: Creates required worker directories
8. **Configuration Validation**: Validates JSON configuration files
9. **Service Startup**: Starts Django server and worker processes
10. **Process Management**: Creates PID files for service management

## 📁 Configuration Files

The bootstrap script uses these configuration files:

- `config/worker_local.json` - Local development worker config
- `config/worker_production.json` - Production worker config  
- `config/detailed_worker_local.json` - Detailed worker config (local only)

## 🛠 Testing the Deployment

### 1. Upload a Job via Web Interface
Navigate to `http://127.0.0.1:8000/qmodel/submit/` and upload the `qmodel.json` file

### 2. Monitor Worker Activity
Watch the terminal for worker logs showing job processing:

```
[INFO] Checking for new jobs...
[INFO] New job found: c7df2f67-b3f6-460b
[INFO] Starting to process new job: c7df2f67-b3f6-460b  
[INFO] [1/6] Processing step 'recording' for Job c7df2f67-b3f6-460b
[INFO] 'recording' progress: 33% (Job c7df2f67-b3f6-460b)
...
[INFO] Job c7df2f67-b3f6-460b finished successfully! Completed 6/6 steps
```

### 3. Check Service Status
```bash
./bootstrap-deploy.sh status
```

Expected output:
```
Service Status:
===================
✓ Django Server: Running (PID: 12345)
✓ SSLH Worker: Running (PID: 12346)  
✓ Detailed Worker: Running (PID: 12347)
===================
```

## 📦 System Requirements

- Python 3.11+
- pip package manager
- Virtual environment support
- 500MB free disk space
- Git (optional, for version control)

## 🔒 Security Notes

- **Development Mode**: Local deployment uses Django development server (not for production)
- **SSL Certificates**: Production mode can generate self-signed certificates
- **Authentication**: API endpoints use Django token authentication
- **Database**: Uses SQLite for simplicity (consider PostgreSQL for production)

## 🚨 Troubleshooting

### Port Already in Use
```bash
# Kill existing processes on port 8000
sudo lsof -ti:8000 | xargs kill -9
```

### Permission Errors
```bash
# Make script executable
chmod +x bootstrap-deploy.sh
```

### Python Version Issues
```bash
# Check Python version
python3 --version
# Should be 3.11+
```

### Missing Dependencies
```bash
# Install missing system packages (macOS)
brew install python@3.11 git

# Install missing system packages (Ubuntu)
sudo apt update
sudo apt install python3.11 python3-pip python3-venv git
```

## 📈 Production Deployment

For production environments:

1. Use a proper WSGI server (Gunicorn is included)
2. Set up a reverse proxy (nginx recommended)
3. Use PostgreSQL instead of SQLite
4. Configure proper SSL certificates
5. Set up log rotation
6. Configure firewall rules
7. Set up monitoring and alerts

Example production command:
```bash
./bootstrap-deploy.sh production --ssl --workers 4 --port 8443
```

## 🎯 Next Steps

After deployment:

1. **Upload Test Job**: Use the `qmodel.json` file to test end-to-end workflow
2. **Monitor Logs**: Watch worker processing in real-time
3. **Check API**: Verify all endpoints are responding correctly
4. **Scale Workers**: Add more worker processes as needed
5. **Configure Production**: Set up proper production environment

---

**Happy spike sorting! 🧠⚡**
