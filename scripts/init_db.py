#!/usr/bin/env python3
"""
Database initialization script for production deployment
"""
import os
import sys
import asyncio
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

# Add the parent directory to the path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app import create_app, db
from backend.app.models.user import User, Role, Permission
from backend.app.models.influencer import Influencer, Platform
from backend.app.models.subscription import SubscriptionPlan, PlanType
from backend.app.services.analytics_service import AnalyticsService

def create_database_extensions(app):
    """Create necessary PostgreSQL extensions"""
    with app.app_context():
        try:
            # Create extensions
            db.engine.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'))
            db.engine.execute(text('CREATE EXTENSION IF NOT EXISTS "pg_trgm";'))
            db.engine.execute(text('CREATE EXTENSION IF NOT EXISTS "btree_gin";'))
            print("✓ Database extensions created successfully")
        except Exception as e:
            print(f"⚠ Warning: Could not create extensions: {e}")

def create_indexes(app):
    """Create performance indexes"""
    with app.app_context():
        try:
            # User indexes
            db.engine.execute(text('''
                CREATE INDEX IF NOT EXISTS idx_users_email_active 
                ON users (email) WHERE is_active = true;
            '''))
            
            # Influencer indexes
            db.engine.execute(text('''
                CREATE INDEX IF NOT EXISTS idx_influencers_platform_followers 
                ON influencers (platform, follower_count DESC);
            '''))
            
            db.engine.execute(text('''
                CREATE INDEX IF NOT EXISTS idx_influencers_username_platform 
                ON influencers (username, platform);
            '''))
            
            # Analytics indexes
            db.engine.execute(text('''
                CREATE INDEX IF NOT EXISTS idx_analytics_influencer_date 
                ON influencer_analytics (influencer_id, created_at DESC);
            '''))
            
            print("✓ Performance indexes created successfully")
        except Exception as e:
            print(f"⚠ Warning: Could not create indexes: {e}")

def create_partitions(app):
    """Create table partitions for large tables"""
    with app.app_context():
        try:
            # Partition analytics table by month
            db.engine.execute(text('''
                -- Create partition for current month if not exists
                DO $$ 
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_class WHERE relname = 'influencer_analytics_' || to_char(now(), 'YYYY_MM')
                    ) THEN
                        EXECUTE format('
                            CREATE TABLE influencer_analytics_%s PARTITION OF influencer_analytics 
                            FOR VALUES FROM (%L) TO (%L)',
                            to_char(now(), 'YYYY_MM'),
                            date_trunc('month', now()),
                            date_trunc('month', now()) + interval '1 month'
                        );
                    END IF;
                END $$;
            '''))
            
            print("✓ Table partitions created successfully")
        except Exception as e:
            print(f"⚠ Warning: Could not create partitions: {e}")

def create_default_roles():
    """Create default user roles and permissions"""
    try:
        # Create permissions
        permissions = [
            'read_dashboard', 'write_dashboard', 'read_analytics', 'write_analytics',
            'read_influencers', 'write_influencers', 'read_reports', 'write_reports',
            'read_payments', 'write_payments', 'admin_access'
        ]
        
        for perm_name in permissions:
            permission = Permission.query.filter_by(name=perm_name).first()
            if not permission:
                permission = Permission(name=perm_name, description=f'{perm_name.replace("_", " ").title()} permission')
                db.session.add(permission)
        
        db.session.commit()
        
        # Create roles
        roles_config = {
            'admin': permissions,
            'premium': ['read_dashboard', 'write_dashboard', 'read_analytics', 'read_influencers', 'read_reports', 'write_reports'],
            'basic': ['read_dashboard', 'read_analytics', 'read_influencers']
        }
        
        for role_name, role_permissions in roles_config.items():
            role = Role.query.filter_by(name=role_name).first()
            if not role:
                role = Role(name=role_name, description=f'{role_name.title()} role')
                db.session.add(role)
                db.session.flush()
                
                # Add permissions to role
                for perm_name in role_permissions:
                    permission = Permission.query.filter_by(name=perm_name).first()
                    if permission:
                        role.permissions.append(permission)
        
        db.session.commit()
        print("✓ Default roles and permissions created successfully")
        
    except Exception as e:
        print(f"✗ Error creating roles: {e}")
        db.session.rollback()

def create_subscription_plans():
    """Create default subscription plans"""
    try:
        plans = [
            {
                'name': 'Basic',
                'plan_type': PlanType.BASIC,
                'price': 2900,  # $29.00 in cents
                'stripe_price_id': 'price_basic_monthly',
                'features': {
                    'influencer_tracking': 100,
                    'analytics_history_months': 3,
                    'reports_per_month': 5,
                    'api_requests_per_day': 1000
                }
            },
            {
                'name': 'Professional',
                'plan_type': PlanType.PROFESSIONAL,
                'price': 9900,  # $99.00 in cents
                'stripe_price_id': 'price_professional_monthly',
                'features': {
                    'influencer_tracking': 1000,
                    'analytics_history_months': 12,
                    'reports_per_month': 50,
                    'api_requests_per_day': 10000
                }
            },
            {
                'name': 'Enterprise',
                'plan_type': PlanType.ENTERPRISE,
                'price': 29900,  # $299.00 in cents
                'stripe_price_id': 'price_enterprise_monthly',
                'features': {
                    'influencer_tracking': -1,  # Unlimited
                    'analytics_history_months': -1,  # Unlimited
                    'reports_per_month': -1,  # Unlimited
                    'api_requests_per_day': -1  # Unlimited
                }
            }
        ]
        
        for plan_data in plans:
            plan = SubscriptionPlan.query.filter_by(plan_type=plan_data['plan_type']).first()
            if not plan:
                plan = SubscriptionPlan(
                    name=plan_data['name'],
                    plan_type=plan_data['plan_type'],
                    price=plan_data['price'],
                    stripe_price_id=plan_data['stripe_price_id'],
                    features=plan_data['features']
                )
                db.session.add(plan)
        
        db.session.commit()
        print("✓ Subscription plans created successfully")
        
    except Exception as e:
        print(f"✗ Error creating subscription plans: {e}")
        db.session.rollback()

def create_admin_user():
    """Create default admin user"""
    try:
        admin_email = os.getenv('ADMIN_EMAIL', 'admin@yourdomain.com')
        admin_password = os.getenv('ADMIN_PASSWORD', 'change-this-password')
        
        # Check if admin already exists
        admin = User.query.filter_by(email=admin_email).first()
        if not admin:
            admin_role = Role.query.filter_by(name='admin').first()
            admin = User(
                email=admin_email,
                username='admin',
                first_name='Admin',
                last_name='User',
                is_active=True,
                is_verified=True
            )
            admin.set_password(admin_password)
            if admin_role:
                admin.roles.append(admin_role)
            
            db.session.add(admin)
            db.session.commit()
            print(f"✓ Admin user created: {admin_email}")
            print(f"⚠ Default password: {admin_password}")
            print("⚠ Please change the admin password after first login!")
        else:
            print(f"ℹ Admin user already exists: {admin_email}")
            
    except Exception as e:
        print(f"✗ Error creating admin user: {e}")
        db.session.rollback()

def main():
    """Main initialization function"""
    print("🚀 Starting database initialization...")
    
    # Create Flask app
    app = create_app()
    
    with app.app_context():
        try:
            # Test database connection
            db.engine.execute(text('SELECT 1'))
            print("✓ Database connection successful")
        except OperationalError as e:
            print(f"✗ Database connection failed: {e}")
            sys.exit(1)
        
        print("\n📋 Creating database structure...")
        
        # Create all tables
        db.create_all()
        print("✓ Database tables created")
        
        # Create extensions and optimizations
        create_database_extensions(app)
        create_indexes(app)
        create_partitions(app)
        
        print("\n👥 Setting up default data...")
        
        # Create default data
        create_default_roles()
        create_subscription_plans()
        create_admin_user()
        
        print("\n✅ Database initialization completed successfully!")
        print("\n📊 Next steps:")
        print("1. Update your .env file with proper configuration")
        print("2. Start the application services with docker-compose")
        print("3. Access the admin panel and change the default password")
        print("4. Configure payment processing with Stripe")

if __name__ == '__main__':
    main()