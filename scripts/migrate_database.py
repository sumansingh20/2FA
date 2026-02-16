#!/usr/bin/env python3
"""
Database migration script for Flask 2FA application.
This script handles database schema migrations and data updates.
"""

import sys
import os
from datetime import datetime

# Add the parent directory to the path so we can import the app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db, User, AuthLog
from sqlalchemy import text

def backup_database():
    """Create a backup of the current database"""
    try:
        # For SQLite databases
        if 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI']:
            import shutil
            db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
            backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(db_path, backup_path)
            print(f"✓ Database backed up to: {backup_path}")
            return backup_path
        else:
            print("⚠️  Manual backup recommended for PostgreSQL databases")
            return None
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return None

def check_table_exists(table_name):
    """Check if a table exists in the database"""
    try:
        result = db.session.execute(text(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}';"))
        return result.fetchone() is not None
    except:
        # For PostgreSQL
        try:
            result = db.session.execute(text(f"SELECT tablename FROM pg_tables WHERE tablename='{table_name}';"))
            return result.fetchone() is not None
        except:
            return False

def migrate_to_v2():
    """Migrate database to version 2 (add indexes and optimize)"""
    print("🔄 Migrating to database version 2...")
    
    try:
        # Add indexes for better performance
        with db.engine.connect() as conn:
            # Check if indexes already exist
            try:
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_auth_logs_email ON auth_logs(email);"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_auth_logs_event_type ON auth_logs(event_type);"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_auth_logs_timestamp ON auth_logs(timestamp);"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_auth_logs_user_id ON auth_logs(user_id);"))
                conn.commit()
                print("✓ Database indexes created successfully")
            except Exception as e:
                print(f"⚠️  Index creation warning: {e}")
        
        return True
    except Exception as e:
        print(f"❌ Migration to v2 failed: {e}")
        return False

def cleanup_old_logs():
    """Clean up old authentication logs (keep last 10000 entries)"""
    try:
        total_logs = AuthLog.query.count()
        if total_logs > 10000:
            # Delete oldest logs
            old_logs = AuthLog.query.order_by(AuthLog.timestamp.asc()).limit(total_logs - 10000).all()
            for log in old_logs:
                db.session.delete(log)
            db.session.commit()
            print(f"✓ Cleaned up {len(old_logs)} old log entries")
        else:
            print(f"✓ Log cleanup not needed ({total_logs} entries)")
        return True
    except Exception as e:
        print(f"❌ Log cleanup failed: {e}")
        return False

def verify_data_integrity():
    """Verify database data integrity"""
    print("🔍 Verifying data integrity...")
    
    issues = []
    
    try:
        # Check for users without email
        users_without_email = User.query.filter(User.email.is_(None)).count()
        if users_without_email > 0:
            issues.append(f"{users_without_email} users without email")
        
        # Check for orphaned auth logs
        orphaned_logs = AuthLog.query.filter(
            AuthLog.user_id.isnot(None),
            ~AuthLog.user_id.in_(db.session.query(User.id))
        ).count()
        if orphaned_logs > 0:
            issues.append(f"{orphaned_logs} orphaned auth logs")
        
        # Check for duplicate emails
        duplicate_emails = db.session.query(User.email).group_by(User.email).having(db.func.count(User.email) > 1).count()
        if duplicate_emails > 0:
            issues.append(f"{duplicate_emails} duplicate email addresses")
        
        if issues:
            print("⚠️  Data integrity issues found:")
            for issue in issues:
                print(f"   - {issue}")
            return False
        else:
            print("✓ Data integrity check passed")
            return True
            
    except Exception as e:
        print(f"❌ Data integrity check failed: {e}")
        return False

def main():
    """Main migration function"""
    print("🔄 Flask 2FA Database Migration")
    print("=" * 50)
    
    with app.app_context():
        try:
            # Create backup
            print("💾 Creating database backup...")
            backup_path = backup_database()
            
            # Check current database state
            print("\n📊 Checking database state...")
            users_table_exists = check_table_exists('users')
            logs_table_exists = check_table_exists('auth_logs')
            
            if not users_table_exists or not logs_table_exists:
                print("❌ Database tables not found. Please run init_database.py first.")
                return 1
            
            print("✓ Database tables found")
            
            # Run migrations
            print("\n🔄 Running migrations...")
            
            # Migrate to v2
            if not migrate_to_v2():
                print("❌ Migration failed")
                return 1
            
            # Clean up old logs
            print("\n🧹 Cleaning up old data...")
            if not cleanup_old_logs():
                print("⚠️  Log cleanup had issues but continuing...")
            
            # Verify data integrity
            print("\n🔍 Verifying data integrity...")
            if not verify_data_integrity():
                print("⚠️  Data integrity issues found but migration completed")
            
            print("\n" + "=" * 50)
            print("🎉 Database migration completed successfully!")
            
            if backup_path:
                print(f"💾 Backup saved to: {backup_path}")
            
            # Show current statistics
            user_count = User.query.count()
            log_count = AuthLog.query.count()
            admin_count = User.query.filter_by(role='admin').count()
            
            print(f"\n📊 Current Database Statistics:")
            print(f"   👥 Total Users: {user_count}")
            print(f"   👑 Admin Users: {admin_count}")
            print(f"   📝 Auth Logs: {log_count}")
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            return 1
    
    return 0

if __name__ == '__main__':
    exit(main())
