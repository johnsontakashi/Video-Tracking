"""
Video Tracking/Influencer Analytics Platform - Main Backend Server
Clean, optimized version with essential features only.
"""

import os
import bcrypt
import sqlite3
from datetime import datetime
from flask import Flask, jsonify, request, g
from flask_cors import CORS
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app, 
     origins=['http://localhost:3000', 'http://localhost:3001', 'http://localhost:3003', 'https://7d562251a9f3.ngrok-free.app/'],
     allow_headers=['Content-Type', 'Authorization'],
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
     supports_credentials=True)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
DATABASE = 'politikos_full.db'
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
FROM_EMAIL = os.environ.get('FROM_EMAIL', 'noreply@politikos.com')

# ============================================================================
# Database Functions
# ============================================================================

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
    """Initialize database with essential tables"""
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
                is_active INTEGER DEFAULT 1,
                email_verified INTEGER DEFAULT 1,
                current_plan TEXT DEFAULT 'free',
                stripe_customer_id TEXT,
                subscription_expires_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_login TEXT
            )
        ''')
        
        # Create sample users if none exist
        existing_users = db.execute('SELECT COUNT(*) as count FROM users').fetchone()
        if existing_users['count'] == 0:
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
                ''', (user['email'], user['password'], user['first_name'], 
                     user['last_name'], user['username'], user['role']))
        
        db.commit()
        logger.info("✅ Database initialized successfully")

# ============================================================================
# Helper Functions
# ============================================================================

def find_user_by_email(email):
    """Find user by email"""
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    return dict(user) if user else None

def find_user_by_id(user_id):
    """Find user by ID"""
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    return dict(user) if user else None

def verify_password(password, hashed_password):
    """Verify password against hash"""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    except:
        return False

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
        return find_user_by_id(user_id)
    except sqlite3.IntegrityError:
        return None

def validate_auth_token(auth_header):
    """Validate Bearer token and return user"""
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    
    token = auth_header.split(' ', 1)[1] if len(auth_header.split(' ', 1)) > 1 else ''
    
    if not token.startswith('mock_access_token_'):
        return None
    
    try:
        user_id = int(token.split('_')[-1])
        return find_user_by_id(user_id)
    except:
        return None

# ============================================================================
# Authentication Routes
# ============================================================================

@app.route('/api/auth/login', methods=['POST'])
def login():
    """User login"""
    try:
        data = request.get_json()
        
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({
                'success': False,
                'error': 'validation_error',
                'message': 'Email and password are required'
            }), 400
        
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
        
        # Return user info and tokens
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
            'message': 'Login failed'
        }), 500

@app.route('/api/auth/signup', methods=['POST'])
def signup():
    """User registration"""
    try:
        data = request.get_json()
        
        # Validate required fields
        email = data.get('email', '').strip()
        password = data.get('password', '')
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
        role = data.get('role', 'user').strip()
        
        if not all([email, password, first_name, last_name]):
            return jsonify({
                'success': False,
                'error': 'validation_error',
                'message': 'All fields are required'
            }), 400
        
        # Check if user already exists
        db = get_db()
        existing_user = db.execute(
            'SELECT id FROM users WHERE email = ?', (email,)
        ).fetchone()
        
        if existing_user:
            return jsonify({
                'success': False,
                'error': 'user_exists',
                'message': 'User with this email already exists'
            }), 409
        
        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Insert new user
        cursor = db.execute(
            '''INSERT INTO users (email, password, first_name, last_name, role, created_at)
               VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)''',
            (email, password_hash, first_name, last_name, role)
        )
        user_id = cursor.lastrowid
        db.commit()
        
        # Get the created user
        user = db.execute(
            'SELECT * FROM users WHERE id = ?', (user_id,)
        ).fetchone()
        
        # Convert SQLite Row to dict and return user info and tokens
        user_dict = dict(user)
        user_response = {k: v for k, v in user_dict.items() if k != 'password'}
        user_response['full_name'] = f"{user_dict['first_name']} {user_dict['last_name']}"
        
        return jsonify({
            'success': True,
            'access_token': f'mock_access_token_{user_dict["id"]}',
            'refresh_token': f'mock_refresh_token_{user_dict["id"]}',
            'token_type': 'Bearer',
            'expires_in': 900,
            'user': user_response,
            'message': 'User registered successfully'
        }), 201
        
    except Exception as e:
        logger.error(f"Signup error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': 'Registration failed'
        }), 500

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """User logout"""
    return jsonify({'success': True, 'message': 'Logged out successfully'})

@app.route('/api/auth/me', methods=['GET'])
def get_me():
    """Get current user info"""
    user = validate_auth_token(request.headers.get('Authorization', ''))
    
    if not user:
        return jsonify({
            'success': False,
            'error': 'unauthorized',
            'message': 'Invalid or missing token'
        }), 401
    
    user_response = {k: v for k, v in user.items() if k != 'password'}
    user_response['full_name'] = f"{user['first_name']} {user['last_name']}"
    
    return jsonify({
        'success': True,
        'user': user_response
    })

# ============================================================================
# User Management Routes
# ============================================================================

@app.route('/api/users', methods=['GET', 'POST'])
def manage_users():
    """Get all users or create new user"""
    user = validate_auth_token(request.headers.get('Authorization', ''))
    
    if not user:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        if request.method == 'GET':
            # Get all users
            db = get_db()
            cursor = db.execute('''
                SELECT id, email, first_name, last_name, username, role, is_active, 
                       email_verified, current_plan, created_at, last_login
                FROM users ORDER BY created_at DESC
            ''')
            
            users = []
            for row in cursor.fetchall():
                user_dict = dict(row)
                user_dict['full_name'] = f"{user_dict['first_name']} {user_dict['last_name']}"
                users.append(user_dict)
            
            return jsonify({
                'success': True,
                'users': users
            })
        
        elif request.method == 'POST':
            # Create new user
            data = request.get_json()
            
            # Validate required fields
            required_fields = ['first_name', 'last_name', 'email', 'password']
            for field in required_fields:
                if not data or not data.get(field):
                    return jsonify({
                        'success': False,
                        'error': 'validation_error',
                        'message': f'{field.replace("_", " ").title()} is required'
                    }), 400
            
            # Check if user already exists
            if find_user_by_email(data['email']):
                return jsonify({
                    'success': False,
                    'error': 'user_exists',
                    'message': 'User with this email already exists'
                }), 409
            
            # Create user
            new_user = create_user(
                email=data['email'],
                password=data['password'],
                first_name=data['first_name'],
                last_name=data['last_name'],
                role=data.get('role', 'guest')
            )
            
            if not new_user:
                return jsonify({
                    'success': False,
                    'error': 'creation_failed',
                    'message': 'Failed to create user'
                }), 500
            
            # Return created user
            user_response = {k: v for k, v in new_user.items() if k != 'password'}
            user_response['full_name'] = f"{new_user['first_name']} {new_user['last_name']}"
            
            return jsonify({
                'success': True,
                'message': 'User created successfully',
                'user': user_response
            }), 201
            
    except Exception as e:
        logger.error(f"Manage users error: {str(e)}")
        return jsonify({'success': False, 'message': 'Operation failed'}), 500

@app.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """Update user"""
    auth_user = validate_auth_token(request.headers.get('Authorization', ''))
    
    if not auth_user:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        # Build update query
        update_fields = []
        params = []
        
        for field in ['first_name', 'last_name', 'email', 'role', 'is_active']:
            if field in data:
                update_fields.append(f"{field} = ?")
                params.append(data[field])
        
        if not update_fields:
            return jsonify({'success': False, 'message': 'No valid fields to update'}), 400
        
        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        params.append(user_id)
        
        db = get_db()
        db.execute(f"UPDATE users SET {', '.join(update_fields)} WHERE id = ?", params)
        db.commit()
        
        updated_user = find_user_by_id(user_id)
        if updated_user:
            user_response = {k: v for k, v in updated_user.items() if k != 'password'}
            user_response['full_name'] = f"{updated_user['first_name']} {updated_user['last_name']}"
            
            return jsonify({
                'success': True,
                'message': 'User updated successfully',
                'user': user_response
            })
        else:
            return jsonify({'success': False, 'message': 'User not found'}), 404
            
    except Exception as e:
        logger.error(f"Update user error: {str(e)}")
        return jsonify({'success': False, 'message': 'Update failed'}), 500

# ============================================================================
# Influencers Routes
# ============================================================================

@app.route('/api/influencers', methods=['GET', 'POST'])
def manage_influencers():
    """Get all influencers or create new influencer"""
    user = validate_auth_token(request.headers.get('Authorization', ''))
    
    if not user:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        if request.method == 'GET':
            # Return mock influencer data for now
            mock_influencers = [
                {
                    'id': 1,
                    'external_id': 'influencer_001',
                    'username': '@johndoe',
                    'display_name': 'John Doe',
                    'platform': 'instagram',
                    'bio': 'Travel blogger and photographer',
                    'profile_image_url': '',
                    'verified': True,
                    'follower_count': 125000,
                    'following_count': 500,
                    'post_count': 850,
                    'engagement_rate': 4.2,
                    'status': 'active',
                    'created_at': '2024-01-15T10:30:00Z',
                    'owner_name': user['first_name'] + ' ' + user['last_name']
                },
                {
                    'id': 2,
                    'external_id': 'influencer_002',
                    'username': '@sarahsmith',
                    'display_name': 'Sarah Smith',
                    'platform': 'youtube',
                    'bio': 'Lifestyle and fashion content creator',
                    'profile_image_url': '',
                    'verified': False,
                    'follower_count': 89000,
                    'following_count': 200,
                    'post_count': 420,
                    'engagement_rate': 6.8,
                    'status': 'active',
                    'created_at': '2024-02-20T14:15:00Z',
                    'owner_name': user['first_name'] + ' ' + user['last_name']
                }
            ]
            
            return jsonify({
                'success': True,
                'influencers': mock_influencers
            })
        
        elif request.method == 'POST':
            # Create new influencer
            data = request.get_json()
            
            # Validate required fields
            required_fields = ['username', 'platform']
            for field in required_fields:
                if not data or not data.get(field):
                    return jsonify({
                        'success': False,
                        'error': 'validation_error',
                        'message': f'{field.replace("_", " ").title()} is required'
                    }), 400
            
            # Create mock influencer response
            new_influencer = {
                'id': 999,  # Mock ID
                'external_id': f"influencer_{data['username']}",
                'username': data.get('username', ''),
                'display_name': data.get('display_name', ''),
                'platform': data.get('platform', ''),
                'bio': data.get('bio', ''),
                'profile_image_url': data.get('profile_image_url', ''),
                'verified': data.get('verified', False),
                'follower_count': data.get('follower_count', 0),
                'following_count': data.get('following_count', 0),
                'post_count': data.get('post_count', 0),
                'engagement_rate': data.get('engagement_rate', 0.0),
                'status': 'active',
                'created_at': datetime.utcnow().isoformat(),
                'owner_name': user['first_name'] + ' ' + user['last_name']
            }
            
            return jsonify({
                'success': True,
                'message': 'Influencer created successfully',
                'influencer': new_influencer
            }), 201
            
    except Exception as e:
        logger.error(f"Manage influencers error: {str(e)}")
        return jsonify({'success': False, 'message': 'Operation failed'}), 500

@app.route('/api/influencers/<int:influencer_id>', methods=['PUT', 'DELETE'])
def update_influencer(influencer_id):
    """Update or delete influencer"""
    user = validate_auth_token(request.headers.get('Authorization', ''))
    
    if not user:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        if request.method == 'PUT':
            data = request.get_json()
            if not data:
                return jsonify({'success': False, 'message': 'No data provided'}), 400
            
            # Mock update response
            updated_influencer = {
                'id': influencer_id,
                'external_id': f"influencer_{data.get('username', '')}",
                'username': data.get('username', ''),
                'display_name': data.get('display_name', ''),
                'platform': data.get('platform', ''),
                'bio': data.get('bio', ''),
                'profile_image_url': data.get('profile_image_url', ''),
                'verified': data.get('verified', False),
                'follower_count': data.get('follower_count', 0),
                'following_count': data.get('following_count', 0),
                'post_count': data.get('post_count', 0),
                'engagement_rate': data.get('engagement_rate', 0.0),
                'status': data.get('status', 'active'),
                'created_at': '2024-01-15T10:30:00Z',
                'owner_name': user['first_name'] + ' ' + user['last_name']
            }
            
            return jsonify({
                'success': True,
                'message': 'Influencer updated successfully',
                'influencer': updated_influencer
            })
        
        elif request.method == 'DELETE':
            return jsonify({
                'success': True,
                'message': 'Influencer deleted successfully'
            })
            
    except Exception as e:
        logger.error(f"Update influencer error: {str(e)}")
        return jsonify({'success': False, 'message': 'Operation failed'}), 500

# ============================================================================
# Health Check Routes
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'database': 'connected',
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/', methods=['GET'])
def root():
    """Root endpoint"""
    return jsonify({
        'message': 'Video Tracking API Server',
        'version': '1.0.0',
        'status': 'running'
    })

# ============================================================================
# Error Handlers
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# ============================================================================
# App Initialization
# ============================================================================

@app.teardown_appcontext
def close_db_connection(exception):
    close_db(exception)

def main():
    """Main function to run the app"""
    # Initialize database
    init_db()
    
    print("✅ Database initialized: politikos_full.db")
    print("🚀 Starting Video Tracking server...")
    print("📧 Sample users:")
    print("   - admin@politikos.com / AdminPass123")
    print("   - analyst@politikos.com / AnalystPass123")
    print("   - user@politikos.com / UserPass123")
    print("🌐 Frontend: http://localhost:3000")
    print("🔧 Backend: http://localhost:5000")
    print("📊 Database: politikos_full.db")
    
    # Run the app
    app.run(debug=True, host='0.0.0.0', port=5000)

if __name__ == '__main__':
    main()