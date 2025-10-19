











#!/usr/bin/env python3
"""
Database initialization script for Flask 2FA application.
This script creates the database tables and populates them with initial data.
"""

import sys
import os
from datetime import datetime

# Add the parent directory to the path so we can import the app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db, User, AuthLog

def create_sample_users():
    """Create sample users for testing"""
    sample_users = [
        {
            'email': 'admin@example.com',
            'password': 'Admin@123',
            'phone': '+1987654321',
            'role': 'admin',
            'status': 'active'
        },
        {
            'email': 'suman@iitp.ac.in',
            'password': 'Suman@123',
            'phone': '+1234567890',
            'role': 'user',
            'status': 'active'
        },
        {
            'email': 'demo@example.com',
            'password': 'Demo@123',
            'phone': '+0987654321',
            'role': 'user',
            'status': 'active'
        },
        {
            'email': 'test@example.com',
            'password': 'Test@123',
            'phone': '+1122334455',
            'role': 'user',
            'status': 'active'
        },
        {
            'email': 'disabled@example.com',
            'password': 'Disabled@123',
            'phone': '+1555666777',
            'role': 'user',
            'status': 'disabled'
        }
    ]
    
    created_count = 0
    for user_data in sample_users:
        existing_user = User.query.filter_by(email=user_data['email']).first()
        if not existing_user:
            user = User(
                email=user_data['email'],
                phone=user_data['phone'],
                role=user_data['role'],
                status=user_data['status']
            )
            user.set_password(user_data['password'])
            db.session.add(user)
            created_count += 1
            print(f"✓ Created user: {user_data['email']} ({user_data['role']})")
        else:
            print(f"- User already exists: {user_data['email']}")
    
    return created_count

def create_sample_logs():
    """Create sample authentication logs for testing"""
    sample_logs = [
        {
            'email': 'admin@example.com',
            'event_type': 'login_success',
            'details': 'Admin login successful',
            'ip_address': '192.168.1.100',
            'delivery_method': 'email'
        },
        {
            'email': 'suman@iitp.ac.in',
            'event_type': 'login_attempt',
            'details': 'User login attempt',
            'ip_address': '192.168.1.101',
            'delivery_method': 'sms'
        },
        {
            'email': 'demo@example.com',
            'event_type': 'otp_verified',
            'details': 'OTP verification successful',
            'ip_address': '192.168.1.102',
            'delivery_method': 'email'
        },
        {
            'email': 'test@example.com',
            'event_type': 'login_failed',
            'details': 'Invalid password',
            'ip_address': '192.168.1.103',
            'delivery_method': 'N/A'
        }
    ]
    
    created_count = 0
    for log_data in sample_logs:
        # Get user ID if user exists
        user = User.query.filter_by(email=log_data['email']).first()
        user_id = user.id if user else None
        
        log = AuthLog(
            user_id=user_id,
            email=log_data['email'],
            event_type=log_data['event_type'],
            details=log_data['details'],
            ip_address=log_data['ip_address'],
            delivery_method=log_data['delivery_method'],
            timestamp=datetime.utcnow()
        )
        db.session.add(log)
        created_count += 1
    
    print(f"✓ Created {created_count} sample log entries")
    return created_count

def main():
    """Main initialization function"""
    print("🔐 Flask 2FA Database Initialization")
    print("=" * 50)
    
    with app.app_context():
        try:
            # Create all tables
            print("📊 Creating database tables...")
            db.create_all()
            print("✓ Database tables created successfully")
            
            # Create sample users
            print("\n👥 Creating sample users...")
            users_created = create_sample_users()
            
            # Create sample logs
            print("\n📝 Creating sample authentication logs...")
            logs_created = create_sample_logs()
            
            # Commit all changes
            db.session.commit()
            
            print("\n" + "=" * 50)
            print("🎉 Database initialization completed successfully!")
            print(f"📊 Users created: {users_created}")
            print(f"📝 Log entries created: {logs_created}")
            print("\n🔑 Default Admin Credentials:")
            print("   Email: admin@example.com")
            print("   Password: Admin@123")
            print("\n🧪 Test User Credentials:")
            print("   Email: suman@iitp.ac.in")
            print("   Password: Suman@123")
            print("   Email: demo@example.com")
            print("   Password: Demo@123")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error initializing database: {e}")
            return 1
    
    return 0

if __name__ == '__main__':
    exit(main())
