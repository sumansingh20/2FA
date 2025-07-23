import os
import secrets
import sqlite3
import hashlib
import time
import json
import requests
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail, Message
from twilio.rest import Client
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
from PIL import Image, ImageDraw, ImageFont
import io
import base64
import random
import string
from gtts import gTTS
import tempfile
from functools import wraps
from collections import defaultdict, Counter
from sqlalchemy import func, desc, and_, or_
import threading
import atexit
from utils.captcha_utils import generate_captcha_challenge, verify_captcha, create_recaptcha_manager
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from twilio.base.exceptions import TwilioException

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')

# Database Configuration
DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL or 'sqlite:///flask_2fa.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
#app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-change-this-in-production')

# Mail Configuration
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', 'Flask 2FA <noreply@flask2fa.com>')

# Initialize extensions
db = SQLAlchemy(app)
migrate = Migrate(app, db)
mail = Mail(app)

# Configuration
USE_EMAIL = os.getenv('USE_EMAIL', 'False').lower() == 'true'
GMAIL_EMAIL = os.getenv('GMAIL_EMAIL', 'your-email@gmail.com')
GMAIL_PASSWORD = os.getenv('GMAIL_PASSWORD', 'your-app-password')

# SMS Configuration (Twilio)
USE_SMS = os.getenv('USE_SMS', 'True').lower() == 'true'
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID', 'your-twilio-account-sid')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN', 'your-twilio-auth-token')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER', '+1234567890')

# Notification Configuration
ENABLE_EMAIL_ALERTS = os.getenv('ENABLE_EMAIL_ALERTS', 'True').lower() == 'true'
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'admin@example.com')
ALERT_THRESHOLD_FAILED_LOGINS = int(os.getenv('ALERT_THRESHOLD_FAILED_LOGINS', 5))
ALERT_THRESHOLD_TIME_WINDOW = int(os.getenv('ALERT_THRESHOLD_TIME_WINDOW', 15))  # minutes

# CAPTCHA Configuration
ENABLE_CAPTCHA = os.getenv('ENABLE_CAPTCHA', 'True').lower() == 'true'
CAPTCHA_TYPE = os.getenv('CAPTCHA_TYPE', 'text')  # 'text' or 'math'
CAPTCHA_ATTEMPTS_THRESHOLD = int(os.getenv('CAPTCHA_ATTEMPTS_THRESHOLD', 3))

# reCAPTCHA Configuration
RECAPTCHA_SITE_KEY = os.getenv('RECAPTCHA_SITE_KEY', '')
RECAPTCHA_SECRET_KEY = os.getenv('RECAPTCHA_SECRET_KEY', '')
RECAPTCHA_V3_SITE_KEY = os.getenv('RECAPTCHA_V3_SITE_KEY', '')
RECAPTCHA_V3_SECRET_KEY = os.getenv('RECAPTCHA_V3_SECRET_KEY', '')
RECAPTCHA_V3_MIN_SCORE = float(os.getenv('RECAPTCHA_V3_MIN_SCORE', '0.5'))
ENABLE_RECAPTCHA_V2 = os.getenv('ENABLE_RECAPTCHA_V2', 'False').lower() == 'true'
ENABLE_RECAPTCHA_V3 = os.getenv('ENABLE_RECAPTCHA_V3', 'False').lower() == 'true'

# Initialize reCAPTCHA managers
recaptcha_v2_manager = None
recaptcha_v3_manager = None

if ENABLE_RECAPTCHA_V2 and RECAPTCHA_SITE_KEY and RECAPTCHA_SECRET_KEY:
    recaptcha_v2_manager = create_recaptcha_manager(RECAPTCHA_SITE_KEY, RECAPTCHA_SECRET_KEY)

if ENABLE_RECAPTCHA_V3 and RECAPTCHA_V3_SITE_KEY and RECAPTCHA_V3_SECRET_KEY:
    recaptcha_v3_manager = create_recaptcha_manager(RECAPTCHA_V3_SITE_KEY, RECAPTCHA_V3_SECRET_KEY)

# Initialize Twilio client
twilio_client = None
if os.getenv('USE_SMS', 'False').lower() == 'true':
    try:
        twilio_client = Client(os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN'))
    except Exception as e:
        print(f"Twilio initialization failed: {e}")
else:
    twilio_client = None

# Database Models
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    role = db.Column(db.String(20), nullable=False, default='user')
    status = db.Column(db.String(20), nullable=False, default='active')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    login_count = db.Column(db.Integer, nullable=False, default=0)
    failed_login_attempts = db.Column(db.Integer, nullable=False, default=0)
    last_failed_login = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    auth_logs = db.relationship('AuthLog', backref='user_obj', lazy=True, cascade='all, delete-orphan')
    activity_logs = db.relationship('ActivityLog', backref='user_obj', lazy=True, cascade='all, delete-orphan')
    notifications = db.relationship('Notification', backref='user_obj', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """Convert user to dictionary"""
        return {
            'id': self.id,
            'email': self.email,
            'phone': self.phone,
            'role': self.role,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'login_count': self.login_count,
            'failed_login_attempts': self.failed_login_attempts
        }
    
    def __repr__(self):
        return f'<User {self.email}>'

class AuthLog(db.Model):
    __tablename__ = 'auth_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    email = db.Column(db.String(120), nullable=False, index=True)
    event_type = db.Column(db.String(50), nullable=False, index=True)
    details = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    delivery_method = db.Column(db.String(20), nullable=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    risk_level = db.Column(db.String(20), nullable=False, default='low')  # low, medium, high, critical
    
    def to_dict(self):
        """Convert auth log to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'email': self.email,
            'event_type': self.event_type,
            'details': self.details or '',
            'ip_address': self.ip_address or '127.0.0.1',
            'user_agent': self.user_agent or '',
            'delivery_method': self.delivery_method or 'N/A',
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'risk_level': self.risk_level
        }
    
    def __repr__(self):
        return f'<AuthLog {self.email} - {self.event_type}>'

class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    email = db.Column(db.String(120), nullable=False, index=True)
    activity_type = db.Column(db.String(50), nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)
    target_user = db.Column(db.String(120), nullable=True)  # For admin activities on other users
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    severity = db.Column(db.String(20), nullable=False, default='info')  # info, warning, error, critical
    
    def to_dict(self):
        """Convert activity log to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'email': self.email,
            'activity_type': self.activity_type,
            'description': self.description,
            'target_user': self.target_user,
            'ip_address': self.ip_address or '127.0.0.1',
            'user_agent': self.user_agent or '',
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'severity': self.severity
        }
    
    def __repr__(self):
        return f'<ActivityLog {self.email} - {self.activity_type}>'

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(50), nullable=False, index=True)  # security, admin, system, info
    severity = db.Column(db.String(20), nullable=False, default='info')  # info, warning, error, critical
    is_read = db.Column(db.Boolean, nullable=False, default=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    email_sent = db.Column(db.Boolean, nullable=False, default=False)
    
    def to_dict(self):
        """Convert notification to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'message': self.message,
            'notification_type': self.notification_type,
            'severity': self.severity,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'email_sent': self.email_sent
        }
    
    def __repr__(self):
        return f'<Notification {self.title}>'

class SecurityAlert(db.Model):
    __tablename__ = 'security_alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    alert_type = db.Column(db.String(50), nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)
    affected_user = db.Column(db.String(120), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    severity = db.Column(db.String(20), nullable=False, default='medium')  # low, medium, high, critical
    status = db.Column(db.String(20), nullable=False, default='active')  # active, resolved, ignored
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    resolved_at = db.Column(db.DateTime, nullable=True)
    resolved_by = db.Column(db.String(120), nullable=True)
    
    def to_dict(self):
        """Convert security alert to dictionary"""
        return {
            'id': self.id,
            'alert_type': self.alert_type,
            'description': self.description,
            'affected_user': self.affected_user,
            'ip_address': self.ip_address,
            'severity': self.severity,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'resolved_by': self.resolved_by
        }
    
    def __repr__(self):
        return f'<SecurityAlert {self.alert_type} - {self.severity}>'

class LoginAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    ip_address = db.Column(db.String(45), nullable=False)
    success = db.Column(db.Boolean, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_agent = db.Column(db.String(255))
    captcha_used = db.Column(db.String(50))
    captcha_success = db.Column(db.Boolean)

# Activity Logging Functions
def log_activity(email, activity_type, description, target_user=None, severity='info', ip_address=None, user_agent=None):
    """Log user/admin activity"""
    try:
        # Get user ID if user exists
        user = User.query.filter_by(email=email).first()
        user_id = user.id if user else None
        
        activity = ActivityLog(
            user_id=user_id,
            email=email,
            activity_type=activity_type,
            description=description,
            target_user=target_user,
            ip_address=ip_address or request.remote_addr if request else '127.0.0.1',
            user_agent=user_agent or request.headers.get('User-Agent', '') if request else '',
            severity=severity
        )
        
        db.session.add(activity)
        db.session.commit()
        
        # Create notification for critical activities
        if severity in ['error', 'critical']:
            create_notification(
                user_id=user_id,
                title=f"Critical Activity: {activity_type}",
                message=description,
                notification_type='security',
                severity=severity
            )
        
        # Send email alert for admin activities
        if activity_type.startswith('admin_') and ENABLE_EMAIL_ALERTS:
            send_activity_alert_email(activity)
            
    except Exception as e:
        print(f"Error logging activity: {e}")

def log_auth_event(email, event_type, details="", ip_address="127.0.0.1", user_agent="", delivery_method=None, risk_level='low'):
    """Log authentication events to database"""
    try:
        # Get user ID if user exists
        user = User.query.filter_by(email=email).first()
        user_id = user.id if user else None
        
        # Get delivery method from session if not provided
        if not delivery_method:
            delivery_method = session.get('delivery_method', 'N/A')
        
        log_entry = AuthLog(
            user_id=user_id,
            email=email,
            event_type=event_type,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            delivery_method=delivery_method,
            risk_level=risk_level
        )
        
        db.session.add(log_entry)
        db.session.commit()
        
        # Check for suspicious activity
        check_suspicious_activity(email, event_type, ip_address)
        
        # Clean up old logs (keep last 10000 entries)
        log_count = AuthLog.query.count()
        if log_count > 10000:
            old_logs = AuthLog.query.order_by(AuthLog.timestamp.asc()).limit(log_count - 10000).all()
            for log in old_logs:
                db.session.delete(log)
            db.session.commit()
            
    except Exception as e:
        db.session.rollback()
        print(f"Error logging auth event: {e}")

def create_notification(user_id, title, message, notification_type='info', severity='info'):
    """Create in-app notification"""
    try:
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            severity=severity
        )
        
        db.session.add(notification)
        db.session.commit()
        
        # Send email for critical notifications
        if severity in ['error', 'critical'] and ENABLE_EMAIL_ALERTS:
            send_notification_email(notification)
            
        return notification
    except Exception as e:
        db.session.rollback()
        print(f"Error creating notification: {e}")
        return None

def create_security_alert(alert_type, description, affected_user=None, ip_address=None, severity='medium'):
    """Create security alert"""
    try:
        alert = SecurityAlert(
            alert_type=alert_type,
            description=description,
            affected_user=affected_user,
            ip_address=ip_address,
            severity=severity
        )
        
        db.session.add(alert)
        db.session.commit()
        
        # Send email alert for high/critical severity
        if severity in ['high', 'critical'] and ENABLE_EMAIL_ALERTS:
            send_security_alert_email(alert)
        
        # Create notification for all admins
        admin_users = User.query.filter_by(role='admin').all()
        for admin in admin_users:
            create_notification(
                user_id=admin.id,
                title=f"Security Alert: {alert_type}",
                message=description,
                notification_type='security',
                severity=severity
            )
        
        return alert
    except Exception as e:
        db.session.rollback()
        print(f"Error creating security alert: {e}")
        return None

def check_suspicious_activity(email, event_type, ip_address):
    """Check for suspicious activity patterns"""
    try:
        # Check for multiple failed login attempts
        if event_type == 'login_failed':
            recent_failures = AuthLog.query.filter(
                and_(
                    AuthLog.email == email,
                    AuthLog.event_type == 'login_failed',
                    AuthLog.timestamp >= datetime.utcnow() - timedelta(minutes=ALERT_THRESHOLD_TIME_WINDOW)
                )
            ).count()
            
            if recent_failures >= ALERT_THRESHOLD_FAILED_LOGINS:
                create_security_alert(
                    alert_type='multiple_failed_logins',
                    description=f'Multiple failed login attempts detected for {email} from IP {ip_address}. {recent_failures} attempts in {ALERT_THRESHOLD_TIME_WINDOW} minutes.',
                    affected_user=email,
                    ip_address=ip_address,
                    severity='high'
                )
        
        # Check for login from new IP
        if event_type == 'login_success':
            previous_ips = db.session.query(AuthLog.ip_address).filter(
                and_(
                    AuthLog.email == email,
                    AuthLog.event_type == 'login_success',
                    AuthLog.ip_address != ip_address
                )
            ).distinct().all()
            
            if previous_ips and len(previous_ips) > 0:
                create_security_alert(
                    alert_type='new_ip_login',
                    description=f'Login from new IP address detected for {email}. New IP: {ip_address}',
                    affected_user=email,
                    ip_address=ip_address,
                    severity='medium'
                )
        
        # Check for rapid successive login attempts
        if event_type in ['login_attempt', 'login_failed']:
            recent_attempts = AuthLog.query.filter(
                and_(
                    AuthLog.email == email,
                    AuthLog.event_type.in_(['login_attempt', 'login_failed']),
                    AuthLog.timestamp >= datetime.utcnow() - timedelta(minutes=5)
                )
            ).count()
            
            if recent_attempts >= 10:
                create_security_alert(
                    alert_type='rapid_login_attempts',
                    description=f'Rapid successive login attempts detected for {email} from IP {ip_address}. {recent_attempts} attempts in 5 minutes.',
                    affected_user=email,
                    ip_address=ip_address,
                    severity='high'
                )
                
    except Exception as e:
        print(f"Error checking suspicious activity: {e}")

# Email Notification Functions
def send_notification_email(notification):
    """Send email notification"""
    try:
        if not notification.user_id:
            return
        
        user = User.query.get(notification.user_id)
        if not user:
            return
        
        subject = f"🔔 {notification.title}"
        
        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px; text-align: center; color: white;">
                    <h2>🔔 Flask 2FA Notification</h2>
                    <h3>{notification.title}</h3>
                </div>
                <div style="padding: 20px; background: #f8f9fa; border-radius: 10px; margin-top: 20px;">
                    <p><strong>Message:</strong></p>
                    <p>{notification.message}</p>
                    <p><strong>Severity:</strong> <span style="color: {'red' if notification.severity == 'critical' else 'orange' if notification.severity == 'error' else 'blue'};">{notification.severity.upper()}</span></p>
                    <p><strong>Time:</strong> {notification.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                </div>
                <div style="text-align: center; margin-top: 20px; color: #666;">
                    <p>This is an automated notification from Flask 2FA Security System.</p>
                </div>
            </body>
        </html>
        """
        
        msg = Message(
            subject=subject,
            recipients=[user.email],
            html=html_body
        )
        
        mail.send(msg)
        
        # Mark as email sent
        notification.email_sent = True
        db.session.commit()
        
    except Exception as e:
        print(f"Error sending notification email: {e}")

def send_security_alert_email(alert):
    """Send security alert email to admins"""
    try:
        admin_users = User.query.filter_by(role='admin').all()
        admin_emails = [admin.email for admin in admin_users]
        
        if not admin_emails:
            admin_emails = [ADMIN_EMAIL]
        
        subject = f"🚨 Security Alert: {alert.alert_type}"
        
        severity_colors = {
            'low': '#28a745',
            'medium': '#ffc107',
            'high': '#fd7e14',
            'critical': '#dc3545'
        }
        
        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #dc3545 0%, #fd7e14 100%); padding: 30px; border-radius: 10px; text-align: center; color: white;">
                    <h2>🚨 Security Alert</h2>
                    <h3>{alert.alert_type.replace('_', ' ').title()}</h3>
                </div>
                <div style="padding: 20px; background: #f8f9fa; border-radius: 10px; margin-top: 20px;">
                    <p><strong>Description:</strong></p>
                    <p>{alert.description}</p>
                    <p><strong>Severity:</strong> <span style="color: {severity_colors.get(alert.severity, '#666')}; font-weight: bold;">{alert.severity.upper()}</span></p>
                    {f'<p><strong>Affected User:</strong> {alert.affected_user}</p>' if alert.affected_user else ''}
                    {f'<p><strong>IP Address:</strong> {alert.ip_address}</p>' if alert.ip_address else ''}
                    <p><strong>Time:</strong> {alert.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                </div>
                <div style="text-align: center; margin-top: 20px;">
                    <a href="http://localhost:5000/admin/security-alerts" style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">View in Admin Panel</a>
                </div>
                <div style="text-align: center; margin-top: 20px; color: #666;">
                    <p>This is an automated security alert from Flask 2FA Security System.</p>
                </div>
            </body>
        </html>
        """
        
        msg = Message(
            subject=subject,
            recipients=admin_emails,
            html=html_body
        )
        
        mail.send(msg)
        
    except Exception as e:
        print(f"Error sending security alert email: {e}")

def send_activity_alert_email(activity):
    """Send activity alert email for admin actions"""
    try:
        admin_users = User.query.filter_by(role='admin').all()
        admin_emails = [admin.email for admin in admin_users if admin.email != activity.email]
        
        if not admin_emails:
            return
        
        subject = f"📋 Admin Activity Alert: {activity.activity_type}"
        
        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #ffc107 0%, #fd7e14 100%); padding: 30px; border-radius: 10px; text-align: center; color: white;">
                    <h2>📋 Admin Activity Alert</h2>
                    <h3>{activity.activity_type.replace('_', ' ').title()}</h3>
                </div>
                <div style="padding: 20px; background: #f8f9fa; border-radius: 10px; margin-top: 20px;">
                    <p><strong>Admin User:</strong> {activity.email}</p>
                    <p><strong>Activity:</strong> {activity.description}</p>
                    {f'<p><strong>Target User:</strong> {activity.target_user}</p>' if activity.target_user else ''}
                    <p><strong>IP Address:</strong> {activity.ip_address}</p>
                    <p><strong>Time:</strong> {activity.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                </div>
                <div style="text-align: center; margin-top: 20px;">
                    <a href="http://localhost:5000/admin/activity-logs" style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">View Activity Logs</a>
                </div>
                <div style="text-align: center; margin-top: 20px; color: #666;">
                    <p>This is an automated activity alert from Flask 2FA Security System.</p>
                </div>
            </body>
        </html>
        """
        
        msg = Message(
            subject=subject,
            recipients=admin_emails,
            html=html_body
        )
        
        mail.send(msg)
        
    except Exception as e:
        print(f"Error sending activity alert email: {e}")

# Background Tasks
def cleanup_old_data():
    """Clean up old data periodically"""
    try:
        with app.app_context():
            # Clean up old notifications (keep last 30 days)
            old_notifications = Notification.query.filter(
                Notification.created_at < datetime.utcnow() - timedelta(days=30)
            ).all()
            
            for notification in old_notifications:
                db.session.delete(notification)
            
            # Clean up old activity logs (keep last 90 days)
            old_activities = ActivityLog.query.filter(
                ActivityLog.timestamp < datetime.utcnow() - timedelta(days=90)
            ).all()
            
            for activity in old_activities:
                db.session.delete(activity)
            
            # Clean up resolved security alerts (keep last 30 days)
            old_alerts = SecurityAlert.query.filter(
                and_(
                    SecurityAlert.status == 'resolved',
                    SecurityAlert.resolved_at < datetime.utcnow() - timedelta(days=30)
                )
            ).all()
            
            for alert in old_alerts:
                db.session.delete(alert)
            
            db.session.commit()
            print(f"Cleaned up old data: {len(old_notifications)} notifications, {len(old_activities)} activities, {len(old_alerts)} alerts")
            
    except Exception as e:
        db.session.rollback()
        print(f"Error cleaning up old data: {e}")

# Initialize scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(func=cleanup_old_data, trigger="interval", hours=24)
scheduler.start()

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())

# Database helper functions
def init_db():
    """Initialize database with default data"""
    db.create_all()
    
    # Create default admin user if not exists
    admin_user = User.query.filter_by(email='admin@example.com').first()
    if not admin_user:
        admin_user = User(
            username='admin',
            email='admin@example.com',
            phone='+1987654321',
            role='admin',
            status='active'
        )
        admin_user.set_password('Admin@123')
        db.session.add(admin_user)
    
    # Create default demo users if not exist
    demo_users = [
        {
            'username': 'suman',
            'email': 'suman@iitp.ac.in',
            'password': 'Suman@123',
            'phone': '+1234567890',
            'role': 'user'
        },
        {
            'username': 'demo',
            'email': 'demo@example.com',
            'password': 'Demo@123',
            'phone': '+0987654321',
            'role': 'user'
        }
    ]
    
    for user_data in demo_users:
        existing_user = User.query.filter_by(email=user_data['email']).first()
        if not existing_user:
            user = User(
                username=user_data['username'],
                email=user_data['email'],
                phone=user_data['phone'],
                role=user_data['role'],
                status='active'
            )
            user.set_password(user_data['password'])
            db.session.add(user)
    
    try:
        db.session.commit()
        print("Database initialized successfully!")
        
        # Log initial setup
        log_activity(
            email='system',
            activity_type='system_init',
            description='Database initialized with default users',
            severity='info'
        )
        
    except Exception as e:
        db.session.rollback()
        print(f"Error initializing database: {e}")

def admin_required(f):
    """Decorator to require admin authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_email' not in session or 'otp_verified' not in session:
            flash('Please login to access admin panel.', 'error')
            return redirect(url_for('index'))
        
        user = User.query.filter_by(email=session['user_email']).first()
        if not user or user.role != 'admin':
            flash('Admin access required.', 'error')
            return redirect(url_for('index'))
        
        return f(*args, **kwargs)
    return decorated_function

def get_user_stats():
    """Get user statistics for dashboard"""
    try:
        total_users = User.query.count()
        active_users = User.query.filter_by(status='active').count()
        admin_users = User.query.filter_by(role='admin').count()
        
        # Recent activity (last 24 hours)
        recent_cutoff = datetime.utcnow() - timedelta(days=1)
        recent_logs = AuthLog.query.filter(AuthLog.timestamp >= recent_cutoff).all()
        
        total_logins_today = AuthLog.query.filter(
            and_(AuthLog.event_type == 'login_success', AuthLog.timestamp >= recent_cutoff)
        ).count()
        
        failed_attempts_today = AuthLog.query.filter(
            and_(AuthLog.event_type == 'login_failed', AuthLog.timestamp >= recent_cutoff)
        ).count()
        
        # Security alerts
        active_alerts = SecurityAlert.query.filter_by(status='active').count()
        critical_alerts = SecurityAlert.query.filter(
            and_(SecurityAlert.status == 'active', SecurityAlert.severity == 'critical')
        ).count()
        
        # Unread notifications
        unread_notifications = Notification.query.filter_by(is_read=False).count()
        
        return {
            'total_users': total_users,
            'active_users': active_users,
            'admin_users': admin_users,
            'total_logins_today': total_logins_today,
            'failed_attempts_today': failed_attempts_today,
            'recent_activity': len(recent_logs),
            'active_alerts': active_alerts,
            'critical_alerts': critical_alerts,
            'unread_notifications': unread_notifications
        }
    except Exception as e:
        print(f"Error getting user stats: {e}")
        return {
            'total_users': 0,
            'active_users': 0,
            'admin_users': 0,
            'total_logins_today': 0,
            'failed_attempts_today': 0,
            'recent_activity': 0,
            'active_alerts': 0,
            'critical_alerts': 0,
            'unread_notifications': 0
        }

def generate_otp():
    """Generate a random 6-digit OTP"""
    return str(random.randint(100000, 999999))

def send_otp_sms(phone, otp):
    """Send OTP via SMS using Twilio"""
    if not USE_SMS or not twilio_client:
        print(f"SMS disabled. OTP for {phone}: {otp}")
        return False
    
    try:
        message_body = f"""🔐 Your 2FA verification code is: {otp}

This code will expire in 5 minutes.

If you didn't request this code, please ignore this message.

- Flask 2FA Demo"""
        
        message = twilio_client.messages.create(
            body=message_body,
            from_=TWILIO_PHONE_NUMBER,
            to=phone
        )
        
        print(f"SMS sent successfully. SID: {message.sid}")
        return True
        
    except TwilioException as e:
        print(f"Twilio SMS sending failed: {e}")
        print(f"Fallback - OTP for {phone}: {otp}")
        return False
    except Exception as e:
        print(f"SMS sending error: {e}")
        print(f"Fallback - OTP for {phone}: {otp}")
        return False

def send_otp_email(email, otp):
    """Send OTP via email or print to console"""
    if USE_EMAIL:
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = GMAIL_EMAIL
            msg['To'] = email
            msg['Subject'] = "Your 2FA Verification Code"
            
            body = f"""
            <html>
                <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px; text-align: center; color: white;">
                        <h2>🔐 Two-Factor Authentication</h2>
                        <p style="font-size: 18px; margin: 20px 0;">Your verification code is:</p>
                        <div style="background: white; color: #333; padding: 15px; border-radius: 8px; font-size: 32px; font-weight: bold; letter-spacing: 5px; margin: 20px 0;">
                            {otp}
                        </div>
                        <p style="font-size: 14px; opacity: 0.9;">This code will expire in 5 minutes.</p>
                        <p style="font-size: 12px; opacity: 0.8;">If you didn't request this code, please ignore this email.</p>
                    </div>
                </body>
            </html>
            """
            
            msg.attach(MIMEText(body, 'html'))
            
            # Gmail SMTP
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(GMAIL_EMAIL, GMAIL_PASSWORD)
            text = msg.as_string()
            server.sendmail(GMAIL_EMAIL, email, text)
            server.quit()
            
            return True
        except Exception as e:
            print(f"Email sending failed: {e}")
            print(f"OTP for {email}: {otp}")
            return False
    else:
        # Print to console for testing
        print(f"\n{'='*50}")
        print(f"🔐 2FA VERIFICATION CODE")
        print(f"{'='*50}")
        print(f"Email: {email}")
        print(f"OTP: {otp}")
        print(f"Expires: {datetime.utcnow() + timedelta(minutes=5)}")
        print(f"{'='*50}\n")
        return True

# Routes
@app.route('/test')
def test():
    """Test route to verify Flask is working"""
    return '<h1>Flask is working!</h1><p>If you see this, the server is running correctly.</p>'

@app.route('/')
def index():
    """Main page - shows login form or redirects based on session state"""
    if 'user_email' in session and 'otp_verified' in session:
        # Get user from database for role checking
        user = User.query.filter_by(email=session['user_email']).first()
        
        # Log page access
        log_activity(
            email=session['user_email'],
            activity_type='page_access',
            description='Accessed main dashboard page',
            severity='info'
        )
        
        return render_template('index.html', state='success', email=session['user_email'], user=user)
    elif 'user_email' in session and 'otp' in session:
        # Show OTP verification form
        delivery_method = session.get('delivery_method', 'email')
        contact_info = session['user_email'] if delivery_method == 'email' else session.get('user_phone', '')
        
        # Return simple OTP verification HTML for now
        return f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>OTP Verification</title>
            <style>
                body {{ font-family: Arial, sans-serif; padding: 20px; background: #f0f0f0; }}
                .container {{ max-width: 400px; margin: 50px auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                h1 {{ color: #333; text-align: center; }}
                .form-group {{ margin: 15px 0; }}
                label {{ display: block; margin-bottom: 5px; color: #555; }}
                input {{ width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; font-size: 16px; }}
                button {{ width: 100%; padding: 12px; background: #007bff; color: white; border: none; border-radius: 5px; font-size: 16px; cursor: pointer; }}
                button:hover {{ background: #0056b3; }}
                .info {{ background: #e7f3ff; padding: 10px; border-radius: 5px; margin: 15px 0; color: #0066cc; }}
                .otp-display {{ background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0; border-left: 4px solid #28a745; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🔐 OTP Verification</h1>
                <div class="info">
                    Check the terminal console for your OTP code!
                </div>
                <div class="otp-display">
                    <strong>Latest OTP:</strong> Check terminal output<br>
                    <strong>Email:</strong> {session['user_email']}<br>
                    <strong>Method:</strong> {delivery_method}
                </div>
                <form method="POST" action="/verify">
                    <div class="form-group">
                        <label for="otp">Enter 6-digit OTP:</label>
                        <input type="text" id="otp" name="otp" required maxlength="6" pattern="[0-9]{{6}}" placeholder="000000">
                    </div>
                    <button type="submit">Verify OTP</button>
                </form>
                <hr style="margin: 20px 0;">
                <p><a href="/logout">← Back to Login</a></p>
            </div>
        </body>
        </html>
        '''
    else:
        # Show login form
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Flask 2FA Login</title>
            <style>
                body {{ font-family: Arial, sans-serif; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }}
                .container {{ max-width: 400px; margin: 50px auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 20px rgba(0,0,0,0.2); }}
                h1 {{ color: #333; text-align: center; margin-bottom: 20px; }}
                .form-group {{ margin: 15px 0; }}
                label {{ display: block; margin-bottom: 5px; color: #555; }}
                input {{ width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; font-size: 16px; }}
                button {{ width: 100%; padding: 12px; background: #007bff; color: white; border: none; border-radius: 5px; font-size: 16px; cursor: pointer; }}
                button:hover {{ background: #0056b3; }}
                .radio-group {{ display: flex; gap: 15px; }}
                .radio-option {{ display: flex; align-items: center; gap: 5px; }}
                .demo-creds {{ background: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 20px; border-left: 4px solid #17a2b8; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🔐 Flask 2FA Login</h1>
                <form method="POST" action="/login">
                    <div class="form-group">
                        <label for="email">Email:</label>
                        <input type="email" id="email" name="email" required value="admin@example.com">
                    </div>
                    <div class="form-group">
                        <label for="password">Password:</label>
                        <input type="password" id="password" name="password" required value="Admin@123">
                    </div>
                    <div class="form-group">
                        <label>Delivery Method:</label>
                        <div class="radio-group">
                            <label class="radio-option">
                                <input type="radio" name="delivery_method" value="email" checked> Email
                            </label>
                            <label class="radio-option">
                                <input type="radio" name="delivery_method" value="sms"> SMS
                            </label>
                        </div>
                    </div>
                    <button type="submit">Login</button>
                </form>
                <div class="demo-creds">
                    <strong>Demo Accounts:</strong><br>
                    <strong>Admin:</strong> admin@example.com / Admin@123<br>
                    <strong>User:</strong> suman@iitp.ac.in / Suman@123<br>
                    <strong>Demo:</strong> demo@example.com / Demo@123
                </div>
            </div>
        </body>
        </html>
        '''

@app.route('/login', methods=['POST'])
def login():
    """Handle login form submission"""
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '')
    delivery_method = request.form.get('delivery_method', 'email')
    captcha_response = request.form.get('captcha_response', '').strip()
    captcha_type = request.form.get('captcha_type', 'custom')
    recaptcha_v2_response = request.form.get('g-recaptcha-response', '')
    recaptcha_v3_token = request.form.get('recaptcha_v3_token', '')
    
    # Check if CAPTCHA is required
    failed_attempts = session.get('failed_login_attempts', 0)
    captcha_required = ENABLE_CAPTCHA and failed_attempts >= CAPTCHA_ATTEMPTS_THRESHOLD
    
    if captcha_required:
        captcha_valid = False
        captcha_details = ""
        
        if captcha_type == 'recaptcha_v2' and ENABLE_RECAPTCHA_V2 and recaptcha_v2_manager:
            # Verify reCAPTCHA v2
            result = recaptcha_v2_manager.verify_recaptcha_v2(recaptcha_v2_response, request.remote_addr)
            captcha_valid = result['success']
            captcha_details = f"reCAPTCHA v2 verification: {result}"
            
        elif captcha_type == 'recaptcha_v3' and ENABLE_RECAPTCHA_V3 and recaptcha_v3_manager:
            # Verify reCAPTCHA v3
            result = recaptcha_v3_manager.verify_recaptcha_v3(
                recaptcha_v3_token, 
                'login', 
                RECAPTCHA_V3_MIN_SCORE, 
                request.remote_addr
            )
            captcha_valid = result['success']
            captcha_details = f"reCAPTCHA v3 verification: score={result.get('score', 0)}, action={result.get('action', '')}"
            
        else:
            # Verify custom CAPTCHA
            captcha_answer = session.get('captcha_answer', '')
            captcha_valid = verify_captcha(captcha_response, captcha_answer)
            captcha_details = f"Custom CAPTCHA verification"
        
        if not captcha_valid:
            log_auth_event(email, 'captcha_failed', f'CAPTCHA verification failed: {captcha_details}', 
                           request.remote_addr, request.headers.get('User-Agent', ''), risk_level='medium')
            
            log_activity(
                email=email,
                activity_type='captcha_failed',
                description=f'CAPTCHA verification failed during login attempt: {captcha_details}',
                severity='warning',
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent', '')
            )
            
            flash('Security verification failed. Please try again.', 'error')
            return redirect(url_for('index'))
        else:
            log_auth_event(email, 'captcha_success', f'CAPTCHA verification successful: {captcha_details}', 
                           request.remote_addr, request.headers.get('User-Agent', ''))
    
    # Log login attempt
    log_auth_event(email, 'login_attempt', f'Attempted login with {delivery_method}', 
                   request.remote_addr, request.headers.get('User-Agent', ''))
    
    log_activity(
        email=email,
        activity_type='login_attempt',
        description=f'User attempted login with {delivery_method} delivery method',
        severity='info',
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent', '')
    )
    
    # Validate credentials using database
    user = User.query.filter_by(email=email).first()
    
    if user and user.check_password(password) and user.status == 'active':
        # Reset failed login attempts on successful login
        session.pop('failed_login_attempts', None)
        session.pop('captcha_answer', None)
        
        # Reset failed login attempts
        user.failed_login_attempts = 0
        user.last_login = datetime.utcnow()
        user.login_count += 1
        db.session.commit()
        
        # Generate and store OTP
        otp = generate_otp()
        session['user_email'] = email
        session['user_phone'] = user.phone
        session['otp'] = otp
        session['delivery_method'] = delivery_method
        session['otp_timestamp'] = datetime.utcnow().isoformat()
        
        # Log successful login
        log_auth_event(email, 'login_success', f'Login successful, OTP requested via {delivery_method}',
                       request.remote_addr, request.headers.get('User-Agent', ''))
        
        log_activity(
            email=email,
            activity_type='login_success',
            description=f'Successful login, OTP requested via {delivery_method}',
            severity='info',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')
        )
        
        # Send OTP based on selected method
        if delivery_method == 'sms':
            phone = user.phone
            if send_otp_sms(phone, otp):
                log_auth_event(email, 'otp_sent', f'OTP sent via SMS to {phone[-4:].rjust(len(phone), "*")}')
                flash(f'OTP sent to {phone[-4:].rjust(len(phone), "*")} via SMS!', 'success')
            else:
                log_auth_event(email, 'otp_failed', 'SMS sending failed')
                flash('Failed to send SMS. Check console for the code.', 'warning')
        else:
            if send_otp_email(email, otp):
                log_auth_event(email, 'otp_sent', f'OTP sent via email to {email}')
                flash('OTP sent to your email successfully!', 'success')
            else:
                log_auth_event(email, 'otp_failed', 'Email sending failed')
                flash('Failed to send email. Check console for the code.', 'warning')
        
        return redirect(url_for('index'))
    else:
        # Increment failed attempts
        failed_attempts = session.get('failed_login_attempts', 0) + 1
        session['failed_login_attempts'] = failed_attempts
        
        # Update failed login attempts
        if user:
            user.failed_login_attempts += 1
            user.last_failed_login = datetime.utcnow()
            db.session.commit()
        
        # Log failed login
        reason = 'Invalid credentials'
        if user and user.status != 'active':
            reason = 'Account disabled'
        
        log_auth_event(email, 'login_failed', reason, request.remote_addr, request.headers.get('User-Agent', ''), risk_level='medium')
        
        log_activity(
            email=email,
            activity_type='login_failed',
            description=f'Failed login attempt: {reason}',
            severity='warning',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')
        )
        
        flash('Invalid email, password, or account disabled!', 'error')
        return redirect(url_for('index'))

@app.route('/verify', methods=['POST'])
def verify_otp():
    """Handle OTP verification"""
    if 'user_email' not in session or 'otp' not in session:
        flash('Session expired. Please login again.', 'error')
        return redirect(url_for('logout'))
    
    entered_otp = request.form.get('otp', '').strip()
    stored_otp = session.get('otp')
    otp_timestamp = session.get('otp_timestamp')
    user_email = session['user_email']
    
    # Check OTP expiration (5 minutes)
    if otp_timestamp:
        otp_time = datetime.fromisoformat(otp_timestamp)
        if datetime.utcnow() - otp_time > timedelta(minutes=5):
            log_auth_event(user_email, 'otp_expired', 'OTP verification failed - expired')
            log_activity(
                email=user_email,
                activity_type='otp_expired',
                description='OTP verification failed - code expired',
                severity='warning'
            )
            flash('OTP has expired. Please login again.', 'error')
            return redirect(url_for('logout'))
    
    # Verify OTP
    if entered_otp == stored_otp:
        session['otp_verified'] = True
        session.pop('otp', None)  # Remove OTP from session for security
        session.pop('otp_timestamp', None)
        
        log_auth_event(user_email, 'otp_verified', 'OTP verification successful')
        log_activity(
            email=user_email,
            activity_type='otp_verified',
            description='OTP verification successful - user authenticated',
            severity='info'
        )
        
        # Create welcome notification
        user = User.query.filter_by(email=user_email).first()
        if user:
            create_notification(
                user_id=user.id,
                title="Welcome Back!",
                message=f"You have successfully logged in from IP {request.remote_addr}",
                notification_type='info',
                severity='info'
            )
        
        flash('2FA verification successful!', 'success')
        return redirect(url_for('index'))
    else:
        log_auth_event(user_email, 'otp_failed', f'Invalid OTP entered: {entered_otp}')
        log_activity(
            email=user_email,
            activity_type='otp_failed',
            description=f'Invalid OTP verification attempt',
            severity='warning'
        )
        flash('Invalid OTP. Please try again.', 'error')
        return redirect(url_for('index'))

@app.route('/resend-otp', methods=['POST'])
def resend_otp():
    """Resend OTP to user"""
    if 'user_email' not in session:
        return jsonify({'success': False, 'message': 'Session expired'})
    
    email = session['user_email']
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'success': False, 'message': 'User not found'})
    
    phone = user.phone
    delivery_method = session.get('delivery_method', 'email')
    otp = generate_otp()
    session['otp'] = otp
    session['otp_timestamp'] = datetime.utcnow().isoformat()
    
    log_activity(
        email=email,
        activity_type='otp_resend',
        description=f'OTP resend requested via {delivery_method}',
        severity='info'
    )
    
    if delivery_method == 'sms' and phone:
        if send_otp_sms(phone, otp):
            log_auth_event(email, 'otp_resent', f'OTP resent via SMS to {phone[-4:].rjust(len(phone), "*")}')
            return jsonify({'success': True, 'message': 'OTP resent via SMS!'})
        else:
            return jsonify({'success': False, 'message': 'Failed to resend SMS'})
    else:
        if send_otp_email(email, otp):
            log_auth_event(email, 'otp_resent', f'OTP resent via email to {email}')
            return jsonify({'success': True, 'message': 'OTP resent via email!'})
        else:
            return jsonify({'success': False, 'message': 'Failed to resend email'})

@app.route('/logout')
def logout():
    """Clear session and redirect to login"""
    if 'user_email' in session:
        log_auth_event(session['user_email'], 'logout', 'User logged out')
        log_activity(
            email=session['user_email'],
            activity_type='logout',
            description='User logged out successfully',
            severity='info'
        )
    session.clear()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('index'))

# CAPTCHA Routes
@app.route('/captcha/generate')
def generate_captcha_route():
    """Generate new CAPTCHA challenge"""
    try:
        captcha_type = request.args.get('type', CAPTCHA_TYPE)
        captcha_data = generate_captcha_challenge(captcha_type)
        
        # Store answer in session
        session['captcha_answer'] = captcha_data['answer']
        
        return jsonify({
            'success': True,
            'captcha': {
                'type': captcha_data['type'],
                'question': captcha_data['question'],
                'image': captcha_data['image'],
                'audio': captcha_data['audio']
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/captcha/verify', methods=['POST'])
def verify_captcha_route():
    """Verify CAPTCHA response"""
    try:
        user_input = request.json.get('response', '').strip()
        correct_answer = session.get('captcha_answer', '')
        
        is_valid = verify_captcha(user_input, correct_answer)
        
        return jsonify({
            'success': True,
            'valid': is_valid
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# reCAPTCHA Routes
@app.route('/recaptcha/verify', methods=['POST'])
def verify_recaptcha_route():
    """Verify reCAPTCHA response"""
    try:
        data = request.get_json()
        captcha_type = data.get('type', 'v2')
        token = data.get('token', '')
        action = data.get('action', 'login')
        
        if captcha_type == 'v2' and ENABLE_RECAPTCHA_V2 and recaptcha_v2_manager:
            result = recaptcha_v2_manager.verify_recaptcha_v2(token, request.remote_addr)
        elif captcha_type == 'v3' and ENABLE_RECAPTCHA_V3 and recaptcha_v3_manager:
            result = recaptcha_v3_manager.verify_recaptcha_v3(
                token, action, RECAPTCHA_V3_MIN_SCORE, request.remote_addr
            )
        else:
            return jsonify({'success': False, 'error': 'reCAPTCHA not configured'})
        
        return jsonify({
            'success': True,
            'valid': result['success'],
            'score': result.get('score'),
            'action': result.get('action'),
            'error_codes': result.get('error_codes', [])
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# Admin Routes (keeping existing ones)
@app.route('/admin')
@admin_required
def admin_dashboard():
    """Admin dashboard with statistics"""
    try:
        log_activity(
            email=session['user_email'],
            activity_type='admin_dashboard_access',
            description='Accessed admin dashboard',
            severity='info'
        )
        
        stats = get_user_stats()
        
        # Get recent logs
        recent_logs = AuthLog.query.order_by(desc(AuthLog.timestamp)).limit(10).all()
        recent_logs_dict = [log.to_dict() for log in recent_logs]
        
        # Event type distribution for charts (last 100 events)
        recent_events = AuthLog.query.order_by(desc(AuthLog.timestamp)).limit(100).all()
        event_counts = Counter([log.event_type for log in recent_events])
        delivery_counts = Counter([log.delivery_method for log in recent_events if log.delivery_method != 'N/A'])
        
        # Get recent security alerts
        recent_alerts = SecurityAlert.query.filter_by(status='active').order_by(desc(SecurityAlert.created_at)).limit(5).all()
        alerts_dict = [alert.to_dict() for alert in recent_alerts]
        
        return render_template('admin/dashboard.html', 
                             stats=stats, 
                             recent_logs=recent_logs_dict,
                             event_counts=dict(event_counts),
                             delivery_counts=dict(delivery_counts),
                             recent_alerts=alerts_dict)
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'error')
        return redirect(url_for('index'))

# Database initialization
def create_tables():
    """Create database tables and initialize data"""
    init_db()

# CLI Commands
@app.cli.command()
def init_database():
    """Initialize the database with default data"""
    init_db()
    print("Database initialized!")

@app.cli.command()
def reset_database():
    """Reset the database (WARNING: This will delete all data!)"""
    db.drop_all()
    init_db()
    print("Database reset complete!")

# CAPTCHA utilities
def generate_text_captcha():
    """Generate a simple text-based CAPTCHA"""
    length = 5
    characters = string.ascii_uppercase + string.digits
    captcha_text = ''.join(random.choice(characters) for _ in range(length))
    
    # Create image
    img = Image.new('RGB', (200, 80), color='white')
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("arial.ttf", 36)
    except:
        font = ImageFont.load_default()
    
    # Add some noise
    for _ in range(100):
        x = random.randint(0, 200)
        y = random.randint(0, 80)
        draw.point((x, y), fill='lightgray')
    
    # Draw text with slight variations
    for i, char in enumerate(captcha_text):
        x = 20 + i * 30 + random.randint(-5, 5)
        y = 20 + random.randint(-10, 10)
        draw.text((x, y), char, fill='black', font=font)
    
    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    return captcha_text, f"data:image/png;base64,{img_str}"

def generate_audio_captcha(text):
    """Generate audio CAPTCHA using gTTS"""
    try:
        # Add spaces between characters for clarity
        spaced_text = ' '.join(text)
        tts = gTTS(text=spaced_text, lang='en', slow=True)
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
            tts.save(tmp_file.name)
            
            # Read and encode as base64
            with open(tmp_file.name, 'rb') as audio_file:
                audio_data = base64.b64encode(audio_file.read()).decode()
            
            # Clean up
            os.unlink(tmp_file.name)
            
            return f"data:audio/mp3;base64,{audio_data}"
    except Exception as e:
        print(f"Audio CAPTCHA generation failed: {e}")
        return None

def verify_recaptcha_v2(response_token):
    """Verify reCAPTCHA v2 response"""
    secret_key = os.getenv('RECAPTCHA_SECRET_KEY')
    if not secret_key:
        return False
    
    verify_url = 'https://www.google.com/recaptcha/api/siteverify'
    data = {
        'secret': secret_key,
        'response': response_token,
        'remoteip': request.remote_addr
    }
    
    try:
        response = requests.post(verify_url, data=data, timeout=10)
        result = response.json()
        return result.get('success', False)
    except Exception as e:
        print(f"reCAPTCHA v2 verification failed: {e}")
        return False

def verify_recaptcha_v3(response_token):
    """Verify reCAPTCHA v3 response"""
    secret_key = os.getenv('RECAPTCHA_V3_SECRET_KEY')
    if not secret_key:
        return False
    
    verify_url = 'https://www.google.com/recaptcha/api/siteverify'
    data = {
        'secret': secret_key,
        'response': response_token,
        'remoteip': request.remote_addr
    }
    
    try:
        response = requests.post(verify_url, data=data, timeout=10)
        result = response.json()
        
        if result.get('success', False):
            score = result.get('score', 0)
            min_score = float(os.getenv('RECAPTCHA_V3_MIN_SCORE', 0.5))
            return score >= min_score
        return False
    except Exception as e:
        print(f"reCAPTCHA v3 verification failed: {e}")
        return False

# Helper functions
def log_login_attempt(username, success, captcha_type=None, captcha_success=None):
    """Log login attempt to database"""
    attempt = LoginAttempt(
        username=username,
        ip_address=request.remote_addr,
        success=success,
        user_agent=request.headers.get('User-Agent', ''),
        captcha_used=captcha_type,
        captcha_success=captcha_success
    )
    db.session.add(attempt)
    db.session.commit()

def create_security_alert(alert_type, message, username=None):
    """Create a security alert"""
    alert = SecurityAlert(
        alert_type=alert_type,
        message=message,
        ip_address=request.remote_addr,
        username=username
    )
    db.session.add(alert)
    db.session.commit()
    
    # Send email notification if enabled
    if os.getenv('ENABLE_EMAIL_ALERTS', 'False').lower() == 'true':
        send_security_alert_email(alert_type, message, username)

def send_security_alert_email(alert_type, message, username=None):
    """Send security alert email to admin"""
    try:
        admin_email = os.getenv('ADMIN_EMAIL')
        if admin_email:
            msg = Message(
                subject=f'Security Alert: {alert_type}',
                recipients=[admin_email],
                body=f"""
Security Alert Details:
Type: {alert_type}
Message: {message}
Username: {username or 'N/A'}
IP Address: {request.remote_addr}
Time: {datetime.utcnow()}
User Agent: {request.headers.get('User-Agent', 'N/A')}
                """
            )
            mail.send(msg)
    except Exception as e:
        print(f"Failed to send security alert email: {e}")

def send_sms_code(phone_number, code):
    """Send SMS verification code"""
    if not twilio_client:
        return False
    
    try:
        message = twilio_client.messages.create(
            body=f'Your verification code is: {code}',
            from_=os.getenv('TWILIO_PHONE_NUMBER'),
            to=phone_number
        )
        return True
    except Exception as e:
        print(f"SMS sending failed: {e}")
        return False

def requires_captcha(username):
    """Check if CAPTCHA is required for this user/IP"""
    if not os.getenv('ENABLE_CAPTCHA', 'False').lower() == 'true':
        return False
    
    threshold = int(os.getenv('CAPTCHA_ATTEMPTS_THRESHOLD', 3))
    
    # Check failed attempts in last 15 minutes
    since = datetime.utcnow() - timedelta(minutes=15)
    failed_attempts = LoginAttempt.query.filter(
        LoginAttempt.username == username,
        LoginAttempt.ip_address == request.remote_addr,
        LoginAttempt.success == False,
        LoginAttempt.timestamp >= since
    ).count()
    
    return failed_attempts >= threshold

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Create default admin user if it doesn't exist
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@example.com',
                role='admin',
                status='active'
            )
            admin.set_password('Admin@123')  # Change this in production!
            db.session.add(admin)
            db.session.commit()
            print("Default admin user created: admin/Admin@123")
    
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
