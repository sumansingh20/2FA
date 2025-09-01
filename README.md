








# 🔐 Flask 2FA Authentication Tool with Database  


A complete Two-Factor Authentication (2FA) web application built with Flask, featuring a beautiful single-page interface, comprehensive admin panel, and persistent database storage using SQLAlchemy.

## ✨ Features

### Core Authentication
- **Single Page Interface**: Login, OTP verification, and success states in one responsive page
- **Multiple Delivery Methods**: Choose between Email or SMS for OTP delivery
- **OTP Generation**: Secure 6-digit OTP with 5-minute expiration
- **Email Integration**: Optional Gmail SMTP support or console fallback
- **SMS Integration**: Twilio SMS service for instant OTP delivery
- **Session Management**: Secure session-based authentication flow

### Admin Panel
- **Real-time Dashboard**: Live statistics, charts, and activity monitoring
- **User Management**: Complete CRUD operations for user accounts
- **Authentication Logs**: Comprehensive audit trail with filtering and pagination
- **Role-based Access**: Admin and user role management
- **Account Status Control**: Enable/disable user accounts

### Database Features
- **Persistent Storage**: SQLAlchemy ORM with SQLite/PostgreSQL support
- **Data Integrity**: Foreign key relationships and constraints
- **Migration Support**: Database versioning and upgrade scripts
- **Performance Optimized**: Proper indexing and query optimization
- **Backup Support**: Automated backup creation during migrations

## 🚀 Quick Start

### 1. Clone and Setup
\`\`\`bash
# Create project directory
mkdir flask_2fa_tool
cd flask_2fa_tool

# Copy all files to this directory
\`\`\`

### 2. Install Dependencies
\`\`\`bash
pip install -r requirements.txt
\`\`\`

### 3. Environment Configuration
Create a `.env` file with your configuration:
\`\`\`bash
# Database Configuration
DATABASE_URL=sqlite:///flask_2fa.db

# Flask Configuration
SECRET_KEY=your-super-secret-key-change-this-in-production

# Email Configuration (Optional)
USE_EMAIL=False
GMAIL_EMAIL=your-email@gmail.com
GMAIL_PASSWORD=your-app-password

# SMS Configuration (Twilio)
USE_SMS=True
TWILIO_ACCOUNT_SID=your-twilio-account-sid
TWILIO_AUTH_TOKEN=your-twilio-auth-token
TWILIO_PHONE_NUMBER=+1234567890
\`\`\`

### 4. Initialize Database
\`\`\`bash
# Option 1: Using the initialization script
python scripts/init_database.py

# Option 2: Using Flask CLI
flask init-database

# Option 3: Automatic initialization (when running the app)
python app.py
\`\`\`

### 5. Run the Application
\`\`\`bash
python app.py
\`\`\`

### 6. Access the App
- **Main App**: `http://localhost:5000`
- **Admin Panel**: `http://localhost:5000/admin` (after logging in as admin)

## 🗄️ Database Setup

### SQLite (Development)
SQLite is used by default and requires no additional setup:
\`\`\`bash
DATABASE_URL=sqlite:///flask_2fa.db
\`\`\`

### PostgreSQL (Production)
For production deployments with PostgreSQL:

1. **Install PostgreSQL**:
   \`\`\`bash
   # Ubuntu/Debian
   sudo apt-get install postgresql postgresql-contrib
   
   # macOS
   brew install postgresql
   \`\`\`

2. **Create Database**:
   \`\`\`sql
   CREATE DATABASE flask_2fa_db;
   CREATE USER flask_user WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE flask_2fa_db TO flask_user;
   \`\`\`

3. **Update Environment**:
   \`\`\`bash
   DATABASE_URL=postgresql://flask_user:your_password@localhost:5432/flask_2fa_db
   \`\`\`

### Database Migration
\`\`\`bash
# Run migration script
python scripts/migrate_database.py

# Or use Flask-Migrate (if you want to add custom migrations)
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
\`\`\`

## 🔧 Configuration

### Default Credentials
- **Admin**: `admin@example.com` / `Admin@123`
- **User**: `suman@iitp.ac.in` / `Suman@123`
- **Demo**: `demo@example.com` / `Demo@123`

### Email Setup (Optional)
To enable email sending via Gmail SMTP:

1. **Enable Gmail SMTP** in `.env`:
   \`\`\`bash
   USE_EMAIL=True
   GMAIL_EMAIL=your-email@gmail.com
   GMAIL_PASSWORD=your-app-password
   \`\`\`

2. **Generate Gmail App Password**:
   - Go to Google Account settings
   - Enable 2-Factor Authentication
   - Generate an App Password for "Mail"
   - Use this App Password in the configuration

### SMS Setup (Twilio)
To enable SMS sending via Twilio:

1. **Create Twilio Account**:
   - Sign up at [twilio.com](https://www.twilio.com)
   - Get a phone number from Twilio Console
   - Note your Account SID and Auth Token

2. **Enable SMS in `.env`**:
   \`\`\`bash
   USE_SMS=True
   TWILIO_ACCOUNT_SID=your-account-sid
   TWILIO_AUTH_TOKEN=your-auth-token
   TWILIO_PHONE_NUMBER=+1234567890
   \`\`\`

## 📁 Project Structure

\`\`\`
flask_2fa_tool/
├── app.py                      # Main Flask application with database models
├── requirements.txt            # Python dependencies
├── .env                        # Environment configuration
├── flask_2fa.db               # SQLite database (auto-created)
├── scripts/
│   ├── init_database.py       # Database initialization script
│   └── migrate_database.py    # Database migration script
├── templates/
│   ├── index.html             # Main authentication interface
│   └── admin/
│       ├── dashboard.html     # Admin dashboard
│   ├── users.html         # User management
│   ├── logs.html          # Authentication logs
│   ├── create_user.html   # Create user form
│   └── edit_user.html     # Edit user form
├── static/
│   ├── style.css              # Main application styles
│   └── admin.css              # Admin panel styles
└── README.md                  # This file
\`\`\`

## 🗃️ Database Schema

### Users Table
- `id`: Primary key
- `email`: Unique email address (indexed)
- `password_hash`: Hashed password using Werkzeug
- `phone`: Phone number for SMS delivery
- `role`: User role (admin/user)
- `status`: Account status (active/disabled)
- `created_at`: Account creation timestamp
- `last_login`: Last successful login
- `login_count`: Total login count

### Auth Logs Table
- `id`: Primary key
- `user_id`: Foreign key to users table
- `email`: User email (indexed)
- `event_type`: Type of authentication event (indexed)
- `details`: Event details and context
- `ip_address`: Client IP address
- `user_agent`: Client user agent
- `delivery_method`: OTP delivery method (email/sms)
- `timestamp`: Event timestamp (indexed)

## 🔒 Security Features

### Authentication Security
- **Password Hashing**: Werkzeug PBKDF2 password hashing
- **Session Management**: Secure Flask sessions with CSRF protection
- **OTP Expiration**: Time-based OTP expiration (5 minutes)
- **Account Lockout**: Disabled account status prevents login
- **Audit Trail**: Comprehensive logging of all authentication events

### Database Security
- **SQL Injection Protection**: SQLAlchemy ORM prevents SQL injection
- **Foreign Key Constraints**: Data integrity through relationships
- **Indexed Queries**: Optimized database performance
- **Data Validation**: Input validation and sanitization

## 📊 Admin Panel Features

### Dashboard Analytics
- **Real-time Statistics**: User counts, login metrics, failed attempts
- **Interactive Charts**: Event distribution and delivery method analytics
- **Activity Monitoring**: Live feed of recent authentication events
- **Auto-refresh**: Real-time updates every 30 seconds

### User Management
- **CRUD Operations**: Create, read, update, delete users
- **Role Management**: Admin and user role assignment
- **Status Control**: Enable/disable user accounts
- **Bulk Operations**: Mass user management capabilities

### Authentication Logs
- **Comprehensive Logging**: All authentication events tracked
- **Advanced Filtering**: Filter by event type, user, date range
- **Pagination**: Efficient handling of large log datasets
- **Export Capabilities**: CSV/PDF export (can be added)

## 🛠️ Development

### Adding New Features
1. **Database Changes**: Update models in `app.py`
2. **Migrations**: Create migration scripts in `scripts/`
3. **Templates**: Add/modify templates in `templates/`
4. **Styles**: Update CSS in `static/`

### Testing
\`\`\`bash
# Run with debug mode
FLASK_ENV=development python app.py

# Test database operations
python scripts/init_database.py
python scripts/migrate_database.py
\`\`\`

### Production Deployment
1. **Environment Variables**: Set production values in `.env`
2. **Database**: Use PostgreSQL for production
3. **Security**: Change secret keys and enable HTTPS
4. **Monitoring**: Implement logging and monitoring
5. **Backup**: Set up automated database backups

## 🚀 Production Deployment

### Environment Setup
\`\`\`bash
# Production environment variables
DATABASE_URL=postgresql://user:pass@localhost:5432/flask_2fa_prod
SECRET_KEY=your-production-secret-key
FLASK_ENV=production
USE_EMAIL=True
USE_SMS=True
\`\`\`

### Database Backup
\`\`\`bash
# PostgreSQL backup
pg_dump flask_2fa_db > backup_$(date +%Y%m%d_%H%M%S).sql

# SQLite backup (automatic in migration script)
python scripts/migrate_database.py
\`\`\`

## 🔍 Troubleshooting

### Common Issues

1. **Database Connection Error**:
   - Check `DATABASE_URL` in `.env`
   - Ensure PostgreSQL is running (if using PostgreSQL)
   - Verify database permissions

2. **Migration Errors**:
   - Backup database before migration
   - Check database schema compatibility
   - Run `python scripts/init_database.py` for fresh setup

3. **Email/SMS Not Working**:
   - Verify credentials in `.env`
   - Check Twilio account balance
   - Ensure Gmail app password is correct

4. **Admin Panel Access**:
   - Ensure user has admin role in database
   - Check session authentication
   - Verify admin routes are accessible

### Debug Mode
\`\`\`bash
FLASK_ENV=development python app.py
\`\`\`

## 📄 License

This project is created for educational and demonstration purposes. Feel free to use and modify as needed.

## 🤝 Contributing

This is a learning tool. Suggestions and improvements are welcome!

---

**Built with ❤️ using Flask, SQLAlchemy, Bootstrap 5, and modern web technologies.**
