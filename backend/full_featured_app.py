import os
import secrets
import bcrypt
import uuid
import sqlite3
import json
from datetime import datetime, timedelta
from flask import Flask, jsonify, request, g
from flask_cors import CORS
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app, origins=['http://localhost:3000', 'http://localhost:3001'])

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY', 'your-sendgrid-api-key-here')
FROM_EMAIL = os.environ.get('FROM_EMAIL', 'noreply@politikos.com')
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
DATABASE = 'politikos_full.db'

def get_db():
    """Get database connection"""
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    """Close database connection"""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    """Initialize comprehensive database schema"""
    with app.app_context():
        db = get_db()
        
        # Users table
        db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                username TEXT UNIQUE,
                role TEXT DEFAULT 'guest',
                is_active BOOLEAN DEFAULT 1,
                email_verified BOOLEAN DEFAULT 1,
                stripe_customer_id TEXT,
                current_plan TEXT DEFAULT 'free',
                subscription_expires_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        ''')
        
        # Password reset tokens
        db.execute('''
            CREATE TABLE IF NOT EXISTS password_reset_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token TEXT UNIQUE NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                used BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Subscription plans
        db.execute('''
            CREATE TABLE IF NOT EXISTS subscription_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_type TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                price DECIMAL(10,2) NOT NULL,
                stripe_product_id TEXT,
                stripe_price_id TEXT,
                influencer_limit INTEGER DEFAULT -1,
                posts_per_month INTEGER DEFAULT -1,
                analytics_retention_days INTEGER DEFAULT 30,
                features TEXT, -- JSON
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Influencers table
        db.execute('''
            CREATE TABLE IF NOT EXISTS influencers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                external_id TEXT NOT NULL,
                username TEXT NOT NULL,
                display_name TEXT,
                platform TEXT NOT NULL,
                bio TEXT,
                profile_image_url TEXT,
                profile_url TEXT,
                verified BOOLEAN DEFAULT 0,
                business_account BOOLEAN DEFAULT 0,
                follower_count INTEGER DEFAULT 0,
                following_count INTEGER DEFAULT 0,
                post_count INTEGER DEFAULT 0,
                location TEXT,
                country_code TEXT,
                language_code TEXT,
                status TEXT DEFAULT 'active',
                last_collected TIMESTAMP,
                collection_frequency INTEGER DEFAULT 24,
                priority_score REAL DEFAULT 1.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE(external_id, platform)
            )
        ''')
        
        # Posts table
        db.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                influencer_id INTEGER NOT NULL,
                external_id TEXT NOT NULL,
                platform TEXT NOT NULL,
                content TEXT,
                content_type TEXT,
                media_urls TEXT, -- JSON
                hashtags TEXT, -- JSON
                mentions TEXT, -- JSON
                likes_count INTEGER DEFAULT 0,
                comments_count INTEGER DEFAULT 0,
                shares_count INTEGER DEFAULT 0,
                views_count INTEGER DEFAULT 0,
                posted_at TIMESTAMP NOT NULL,
                language_detected TEXT,
                location_data TEXT, -- JSON
                raw_data TEXT, -- JSON
                collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (influencer_id) REFERENCES influencers (id),
                UNIQUE(external_id, platform)
            )
        ''')
        
        # Comments table
        db.execute('''
            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER NOT NULL,
                external_id TEXT NOT NULL,
                content TEXT NOT NULL,
                author_username TEXT,
                author_display_name TEXT,
                likes_count INTEGER DEFAULT 0,
                replies_count INTEGER DEFAULT 0,
                posted_at TIMESTAMP NOT NULL,
                language_detected TEXT,
                collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (post_id) REFERENCES posts (id)
            )
        ''')
        
        # Analytics table
        db.execute('''
            CREATE TABLE IF NOT EXISTS influencer_analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                influencer_id INTEGER NOT NULL,
                influence_score REAL NOT NULL,
                engagement_rate REAL DEFAULT 0.0,
                consistency_score REAL DEFAULT 0.0,
                growth_rate REAL DEFAULT 0.0,
                sentiment_positive REAL DEFAULT 0.0,
                sentiment_neutral REAL DEFAULT 0.0,
                sentiment_negative REAL DEFAULT 0.0,
                sentiment_compound REAL DEFAULT 0.0,
                avg_likes REAL DEFAULT 0.0,
                avg_comments REAL DEFAULT 0.0,
                avg_shares REAL DEFAULT 0.0,
                top_hashtags TEXT, -- JSON
                top_keywords TEXT, -- JSON
                period_start TIMESTAMP NOT NULL,
                period_end TIMESTAMP NOT NULL,
                posts_analyzed INTEGER DEFAULT 0,
                computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (influencer_id) REFERENCES influencers (id)
            )
        ''')
        
        # Collection tasks
        db.execute('''
            CREATE TABLE IF NOT EXISTS collection_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT UNIQUE NOT NULL,
                influencer_id INTEGER NOT NULL,
                platform TEXT NOT NULL,
                collection_type TEXT NOT NULL,
                parameters TEXT, -- JSON
                status TEXT DEFAULT 'pending',
                priority INTEGER DEFAULT 5,
                worker_id TEXT,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                duration_seconds REAL,
                items_collected INTEGER DEFAULT 0,
                items_failed INTEGER DEFAULT 0,
                result_data TEXT, -- JSON
                error_message TEXT,
                error_traceback TEXT,
                retry_count INTEGER DEFAULT 0,
                max_retries INTEGER DEFAULT 3,
                rate_limit_hit BOOLEAN DEFAULT 0,
                next_retry_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (influencer_id) REFERENCES influencers (id)
            )
        ''')
        
        # Subscriptions
        db.execute('''
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                plan_id INTEGER NOT NULL,
                stripe_subscription_id TEXT UNIQUE,
                stripe_customer_id TEXT,
                status TEXT NOT NULL,
                current_period_start TIMESTAMP NOT NULL,
                current_period_end TIMESTAMP NOT NULL,
                trial_start TIMESTAMP,
                trial_end TIMESTAMP,
                activated_at TIMESTAMP,
                cancelled_at TIMESTAMP,
                usage_data TEXT, -- JSON
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (plan_id) REFERENCES subscription_plans (id)
            )
        ''')
        
        # Payments
        db.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                subscription_id INTEGER,
                plan_id INTEGER,
                stripe_payment_intent_id TEXT UNIQUE,
                stripe_invoice_id TEXT,
                amount DECIMAL(10,2) NOT NULL,
                currency TEXT DEFAULT 'USD',
                status TEXT NOT NULL,
                plan_type TEXT,
                description TEXT,
                payment_method_type TEXT,
                last4 TEXT,
                failure_reason TEXT,
                refund_amount DECIMAL(10,2),
                refund_reason TEXT,
                paid_at TIMESTAMP,
                failed_at TIMESTAMP,
                refunded_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (subscription_id) REFERENCES subscriptions (id),
                FOREIGN KEY (plan_id) REFERENCES subscription_plans (id)
            )
        ''')
        
        # Usage records
        db.execute('''
            CREATE TABLE IF NOT EXISTS usage_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                subscription_id INTEGER,
                period_start TIMESTAMP NOT NULL,
                period_end TIMESTAMP NOT NULL,
                influencers_tracked INTEGER DEFAULT 0,
                posts_analyzed INTEGER DEFAULT 0,
                comments_analyzed INTEGER DEFAULT 0,
                api_calls_made INTEGER DEFAULT 0,
                storage_used_gb REAL DEFAULT 0.0,
                instagram_posts INTEGER DEFAULT 0,
                youtube_posts INTEGER DEFAULT 0,
                tiktok_posts INTEGER DEFAULT 0,
                twitter_posts INTEGER DEFAULT 0,
                sentiment_analyses INTEGER DEFAULT 0,
                trend_analyses INTEGER DEFAULT 0,
                competitor_analyses INTEGER DEFAULT 0,
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (subscription_id) REFERENCES subscriptions (id)
            )
        ''')
        
        # Create indexes for performance
        db.executescript('''
            CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
            CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
            CREATE INDEX IF NOT EXISTS idx_tokens_token ON password_reset_tokens(token);
            CREATE INDEX IF NOT EXISTS idx_tokens_expires ON password_reset_tokens(expires_at);
            CREATE INDEX IF NOT EXISTS idx_influencers_user ON influencers(user_id);
            CREATE INDEX IF NOT EXISTS idx_influencers_platform ON influencers(platform);
            CREATE INDEX IF NOT EXISTS idx_influencers_status ON influencers(status);
            CREATE INDEX IF NOT EXISTS idx_posts_influencer ON posts(influencer_id);
            CREATE INDEX IF NOT EXISTS idx_posts_posted_at ON posts(posted_at);
            CREATE INDEX IF NOT EXISTS idx_comments_post ON comments(post_id);
            CREATE INDEX IF NOT EXISTS idx_analytics_influencer ON influencer_analytics(influencer_id);
            CREATE INDEX IF NOT EXISTS idx_tasks_status ON collection_tasks(status);
            CREATE INDEX IF NOT EXISTS idx_tasks_priority ON collection_tasks(priority);
            CREATE INDEX IF NOT EXISTS idx_subscriptions_user ON subscriptions(user_id);
            CREATE INDEX IF NOT EXISTS idx_payments_user ON payments(user_id);
            CREATE INDEX IF NOT EXISTS idx_usage_user ON usage_records(user_id);
        ''')
        
        # Check if we have any data, if not, create sample data
        cursor = db.execute('SELECT COUNT(*) FROM users')
        user_count = cursor.fetchone()[0]
        
        if user_count == 0:
            # Create sample users
            sample_users = [
                {
                    'email': 'admin@politikos.com',
                    'password': bcrypt.hashpw('AdminPass123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
                    'first_name': 'Admin',
                    'last_name': 'User',
                    'username': 'admin',
                    'role': 'admin'
                },
                {
                    'email': 'analyst@politikos.com', 
                    'password': bcrypt.hashpw('AnalystPass123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
                    'first_name': 'Data',
                    'last_name': 'Analyst',
                    'username': 'analyst',
                    'role': 'analyst'
                },
                {
                    'email': 'user@politikos.com',
                    'password': bcrypt.hashpw('UserPass123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
                    'first_name': 'Regular',
                    'last_name': 'User',
                    'username': 'regularuser',
                    'role': 'guest'
                }
            ]
            
            for user in sample_users:
                db.execute('''
                    INSERT INTO users (email, password, first_name, last_name, username, role)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (user['email'], user['password'], user['first_name'], user['last_name'], user['username'], user['role']))
            
            # Create sample subscription plans
            plans = [
                {
                    'plan_type': 'free',
                    'name': 'Free Plan',
                    'price': 0.00,
                    'influencer_limit': 3,
                    'posts_per_month': 100,
                    'analytics_retention_days': 7,
                    'features': json.dumps(['basic_analytics', 'manual_tracking'])
                },
                {
                    'plan_type': 'starter',
                    'name': 'Starter Plan',
                    'price': 29.99,
                    'influencer_limit': 25,
                    'posts_per_month': 1000,
                    'analytics_retention_days': 30,
                    'features': json.dumps(['advanced_analytics', 'automated_tracking', 'sentiment_analysis'])
                },
                {
                    'plan_type': 'professional',
                    'name': 'Professional Plan', 
                    'price': 99.99,
                    'influencer_limit': 100,
                    'posts_per_month': 5000,
                    'analytics_retention_days': 90,
                    'features': json.dumps(['premium_analytics', 'real_time_tracking', 'competitor_analysis', 'custom_reports'])
                },
                {
                    'plan_type': 'enterprise',
                    'name': 'Enterprise Plan',
                    'price': 299.99,
                    'influencer_limit': -1,
                    'posts_per_month': -1,
                    'analytics_retention_days': 365,
                    'features': json.dumps(['enterprise_analytics', 'api_access', 'white_label', 'dedicated_support'])
                }
            ]
            
            for plan in plans:
                db.execute('''
                    INSERT INTO subscription_plans (plan_type, name, price, influencer_limit, posts_per_month, analytics_retention_days, features)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (plan['plan_type'], plan['name'], plan['price'], plan['influencer_limit'], plan['posts_per_month'], plan['analytics_retention_days'], plan['features']))
            
            # Create sample influencers
            sample_influencers = [
                {
                    'user_id': 2,  # analyst user
                    'external_id': 'techguru123',
                    'username': 'techguru123',
                    'display_name': 'Tech Guru',
                    'platform': 'instagram',
                    'bio': 'Technology enthusiast and reviewer',
                    'verified': 1,
                    'follower_count': 125000,
                    'following_count': 850,
                    'post_count': 342
                },
                {
                    'user_id': 2,
                    'external_id': 'fashionista_rio',
                    'username': 'fashionista_rio',
                    'display_name': 'Fashionista Rio',
                    'platform': 'instagram',
                    'bio': 'Fashion trends from Rio de Janeiro',
                    'verified': 0,
                    'follower_count': 89000,
                    'following_count': 1200,
                    'post_count': 523
                },
                {
                    'user_id': 3,  # regular user
                    'external_id': 'fitness_coach_sp',
                    'username': 'fitness_coach_sp',
                    'display_name': 'Fitness Coach SP',
                    'platform': 'youtube',
                    'bio': 'Fitness coach from São Paulo',
                    'verified': 1,
                    'follower_count': 67000,
                    'following_count': 423,
                    'post_count': 189
                }
            ]
            
            for influencer in sample_influencers:
                db.execute('''
                    INSERT INTO influencers (user_id, external_id, username, display_name, platform, bio, verified, follower_count, following_count, post_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (influencer['user_id'], influencer['external_id'], influencer['username'], influencer['display_name'], 
                     influencer['platform'], influencer['bio'], influencer['verified'], influencer['follower_count'],
                     influencer['following_count'], influencer['post_count']))
        
        db.commit()
        print(f"✅ Full database initialized: {DATABASE}")

@app.teardown_appcontext
def close_db_handler(error):
    close_db()

def find_user_by_email(email):
    """Find user by email"""
    db = get_db()
    cursor = db.execute('SELECT * FROM users WHERE email = ?', (email,))
    row = cursor.fetchone()
    if row:
        return dict(row)
    return None

def find_user_by_id(user_id):
    """Find user by ID"""
    db = get_db()
    cursor = db.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    row = cursor.fetchone()
    if row:
        return dict(row)
    return None

def create_user(email, password, first_name, last_name, role='guest'):
    """Create new user"""
    db = get_db()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    try:
        cursor = db.execute('''
            INSERT INTO users (email, password, first_name, last_name, role)
            VALUES (?, ?, ?, ?, ?)
        ''', (email, hashed_password, first_name, last_name, role))
        user_id = cursor.lastrowid
        db.commit()
        
        # Return the created user
        return find_user_by_id(user_id)
    except sqlite3.IntegrityError:
        return None

def verify_password(password, hashed_password):
    """Verify password against hash"""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    except:
        return False

def send_email(to_email, subject, content):
    """Send email using SendGrid"""
    try:
        sg = SendGridAPIClient(api_key=SENDGRID_API_KEY)
        from_email = Email(FROM_EMAIL)
        to_email = To(to_email)
        content = Content("text/html", content)
        mail = Mail(from_email, to_email, subject, content)
        
        response = sg.client.mail.send.post(request_body=mail.get())
        return response.status_code == 202
    except Exception as e:
        print(f"Failed to send email to {to_email}: {str(e)}")
        return False

# Authentication routes
@app.route('/api/auth/signup', methods=['POST'])
def signup():
    try:
        data = request.get_json()
        
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({
                'success': False,
                'error': 'validation_error',
                'message': 'Email and password are required'
            }), 400
        
        # Check if user exists
        existing_user = find_user_by_email(data['email'])
        if existing_user:
            return jsonify({
                'success': False,
                'error': 'user_exists',
                'message': 'User with this email already exists'
            }), 400
        
        # Create new user
        new_user = create_user(
            email=data['email'].lower().strip(),
            password=data['password'],
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', ''),
            role=data.get('role', 'guest')
        )
        
        if not new_user:
            return jsonify({
                'success': False,
                'error': 'creation_failed',
                'message': 'Failed to create user'
            }), 500
        
        # Return user info (without password)
        user_response = {k: v for k, v in new_user.items() if k != 'password'}
        user_response['full_name'] = f"{new_user['first_name']} {new_user['last_name']}"
        
        return jsonify({
            'success': True,
            'message': 'User registered successfully',
            'user': user_response
        }), 201
        
    except Exception as e:
        logger.error(f"Signup error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': 'Registration failed'
        }), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({
                'success': False,
                'error': 'validation_error',
                'message': 'Email and password are required'
            }), 400
        
        # Find user
        user = find_user_by_email(data['email'])
        
        if not user or not verify_password(data['password'], user['password']):
            return jsonify({
                'success': False,
                'error': 'authentication_failed',
                'message': 'Invalid email or password'
            }), 401
        
        # Update last login
        db = get_db()
        db.execute('UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?', (user['id'],))
        db.commit()
        
        # Return user info and mock tokens
        user_response = {k: v for k, v in user.items() if k != 'password'}
        user_response['full_name'] = f"{user['first_name']} {user['last_name']}"
        
        return jsonify({
            'success': True,
            'access_token': f'mock_access_token_{user["id"]}',
            'refresh_token': f'mock_refresh_token_{user["id"]}',
            'token_type': 'Bearer',
            'expires_in': 900,
            'user': user_response
        }), 200
        
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': f'Login failed: {str(e)}'
        }), 500

@app.route('/api/auth/me', methods=['GET'])
def get_me():
    # Mock authenticated user response - in real app would validate token
    auth_header = request.headers.get('Authorization', '')
    if 'mock_access_token' not in auth_header:
        return jsonify({
            'success': False,
            'error': 'unauthorized',
            'message': 'Invalid or missing token'
        }), 401
    
    # Extract user ID from mock token
    try:
        user_id = int(auth_header.split('_')[-1])
        user = find_user_by_id(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'error': 'user_not_found',
                'message': 'User not found'
            }), 404
        
        user_response = {k: v for k, v in user.items() if k != 'password'}
        user_response['full_name'] = f"{user['first_name']} {user['last_name']}"
        
        return jsonify({
            'success': True,
            'user': user_response
        })
    except:
        return jsonify({
            'success': False,
            'error': 'invalid_token',
            'message': 'Invalid token format'
        }), 401

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    return jsonify({
        'success': True,
        'message': 'Logged out successfully'
    })

@app.route('/api/auth/request-password-reset', methods=['POST'])
def request_password_reset():
    try:
        data = request.get_json()
        
        if not data or not data.get('email'):
            return jsonify({
                'success': False,
                'error': 'validation_error',
                'message': 'Email is required'
            }), 400
        
        user = find_user_by_email(data['email'])
        
        if user:
            # Generate reset token
            reset_token = secrets.token_urlsafe(32)
            expires_at = datetime.utcnow() + timedelta(hours=1)
            
            db = get_db()
            db.execute('''
                INSERT INTO password_reset_tokens (user_id, token, expires_at)
                VALUES (?, ?, ?)
            ''', (user['id'], reset_token, expires_at))
            db.commit()
            
            # Send reset email
            reset_link = f"{FRONTEND_URL}/reset-password?token={reset_token}"
            subject = "Password Reset - POLITIKOS"
            content = f"""
            <h2>Password Reset Request</h2>
            <p>Click the link below to reset your password:</p>
            <a href="{reset_link}">Reset Password</a>
            <p>This link expires in 1 hour.</p>
            """
            
            email_sent = send_email(user['email'], subject, content)
            if not email_sent:
                logger.error(f"Failed to send password reset email to {user['email']}")
        
        # Always return success for security
        return jsonify({
            'success': True,
            'message': 'If the email exists, password reset instructions have been sent'
        }), 200
        
    except Exception as e:
        logger.error(f"Password reset error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': 'Password reset request failed'
        }), 500

# User management routes
@app.route('/api/users', methods=['GET'])
def get_users():
    try:
        # Mock auth check
        auth_header = request.headers.get('Authorization', '')
        if 'mock_access_token' not in auth_header:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        
        db = get_db()
        cursor = db.execute('''
            SELECT id, email, first_name, last_name, username, role, is_active, email_verified, 
                   current_plan, created_at, last_login
            FROM users ORDER BY created_at DESC
        ''')
        
        users = []
        for row in cursor.fetchall():
            user = dict(row)
            user['full_name'] = f"{user['first_name']} {user['last_name']}"
            users.append(user)
        
        return jsonify({
            'success': True,
            'users': users
        })
    except Exception as e:
        logger.error(f"Get users error: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to fetch users'}), 500

@app.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    try:
        # Mock auth check
        auth_header = request.headers.get('Authorization', '')
        if 'mock_access_token' not in auth_header:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        
        data = request.get_json()
        
        db = get_db()
        db.execute('''
            UPDATE users 
            SET first_name = ?, last_name = ?, username = ?, role = ?, is_active = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (data.get('first_name'), data.get('last_name'), data.get('username'), 
              data.get('role'), data.get('is_active', True), user_id))
        
        db.commit()
        
        updated_user = find_user_by_id(user_id)
        user_response = {k: v for k, v in updated_user.items() if k != 'password'}
        user_response['full_name'] = f"{updated_user['first_name']} {updated_user['last_name']}"
        
        return jsonify({
            'success': True,
            'user': user_response
        })
    except Exception as e:
        logger.error(f"Update user error: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to update user'}), 500

# Influencer management routes
@app.route('/api/influencers', methods=['GET'])
def get_influencers():
    try:
        # Mock auth check
        auth_header = request.headers.get('Authorization', '')
        if 'mock_access_token' not in auth_header:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        
        db = get_db()
        cursor = db.execute('''
            SELECT i.*, u.first_name || ' ' || u.last_name as owner_name
            FROM influencers i
            LEFT JOIN users u ON i.user_id = u.id
            ORDER BY i.follower_count DESC
        ''')
        
        influencers = []
        for row in cursor.fetchall():
            influencer = dict(row)
            
            # Calculate engagement rate (mock)
            if influencer['follower_count'] > 0:
                influencer['engagement_rate'] = round((influencer['follower_count'] * 0.03), 2)
            else:
                influencer['engagement_rate'] = 0.0
                
            influencers.append(influencer)
        
        return jsonify({
            'success': True,
            'influencers': influencers
        })
    except Exception as e:
        logger.error(f"Get influencers error: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to fetch influencers'}), 500

@app.route('/api/influencers', methods=['POST'])
def create_influencer():
    try:
        # Mock auth check
        auth_header = request.headers.get('Authorization', '')
        if 'mock_access_token' not in auth_header:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        
        data = request.get_json()
        user_id = int(auth_header.split('_')[-1])  # Extract user ID from token
        
        db = get_db()
        cursor = db.execute('''
            INSERT INTO influencers (user_id, external_id, username, display_name, platform, bio, 
                                   follower_count, following_count, post_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, data.get('external_id', data['username']), data['username'], 
              data.get('display_name'), data['platform'], data.get('bio', ''),
              data.get('follower_count', 0), data.get('following_count', 0), data.get('post_count', 0)))
        
        influencer_id = cursor.lastrowid
        db.commit()
        
        # Get the created influencer
        cursor = db.execute('SELECT * FROM influencers WHERE id = ?', (influencer_id,))
        influencer = dict(cursor.fetchone())
        
        return jsonify({
            'success': True,
            'influencer': influencer
        }), 201
    except Exception as e:
        logger.error(f"Create influencer error: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to create influencer'}), 500

# Analytics routes
@app.route('/api/analytics/overview', methods=['GET'])
def get_analytics_overview():
    try:
        # Mock auth check
        auth_header = request.headers.get('Authorization', '')
        if 'mock_access_token' not in auth_header:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        
        user_id = int(auth_header.split('_')[-1])
        
        db = get_db()
        
        # Get user's influencer count
        cursor = db.execute('SELECT COUNT(*) FROM influencers WHERE user_id = ?', (user_id,))
        influencer_count = cursor.fetchone()[0]
        
        # Get total posts
        cursor = db.execute('''
            SELECT COUNT(*) FROM posts p 
            JOIN influencers i ON p.influencer_id = i.id 
            WHERE i.user_id = ?
        ''', (user_id,))
        posts_count = cursor.fetchone()[0]
        
        # Mock analytics data
        analytics = {
            'total_influencers': influencer_count,
            'total_posts': posts_count,
            'total_engagement': 45623,
            'avg_engagement_rate': 3.2,
            'top_platforms': [
                {'platform': 'instagram', 'count': 8},
                {'platform': 'youtube', 'count': 4},
                {'platform': 'tiktok', 'count': 3},
                {'platform': 'twitter', 'count': 2}
            ],
            'engagement_trend': [
                {'date': '2024-01-01', 'engagement': 1200},
                {'date': '2024-01-02', 'engagement': 1350},
                {'date': '2024-01-03', 'engagement': 1180},
                {'date': '2024-01-04', 'engagement': 1420},
                {'date': '2024-01-05', 'engagement': 1680},
                {'date': '2024-01-06', 'engagement': 1550},
                {'date': '2024-01-07', 'engagement': 1750}
            ]
        }
        
        return jsonify({
            'success': True,
            'analytics': analytics
        })
    except Exception as e:
        logger.error(f"Get analytics error: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to fetch analytics'}), 500

# Subscription routes
@app.route('/api/subscription/plans', methods=['GET'])
def get_subscription_plans():
    try:
        db = get_db()
        cursor = db.execute('SELECT * FROM subscription_plans WHERE is_active = 1 ORDER BY price ASC')
        
        plans = []
        for row in cursor.fetchall():
            plan = dict(row)
            if plan['features']:
                plan['features'] = json.loads(plan['features'])
            plans.append(plan)
        
        return jsonify({
            'success': True,
            'plans': plans
        })
    except Exception as e:
        logger.error(f"Get plans error: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to fetch plans'}), 500

if __name__ == '__main__':
    init_db()
    print("🚀 Starting POLITIKOS full-featured server...")
    print("📧 Sample users:")
    print("   - admin@politikos.com / AdminPass123")
    print("   - analyst@politikos.com / AnalystPass123") 
    print("   - user@politikos.com / UserPass123")
    print("🌐 Frontend: http://localhost:3000")
    print("🔧 Backend: http://localhost:5000")
    print(f"📬 Email service: SendGrid ({'✅ Configured' if SENDGRID_API_KEY != 'your-sendgrid-api-key-here' else '❌ Not configured'})")
    print(f"📊 Database: {DATABASE}")
    
    app.run(debug=True, host='0.0.0.0', port=5000)