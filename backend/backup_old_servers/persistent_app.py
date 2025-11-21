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
DATABASE = 'politikos.db'

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
    """Initialize database with tables and sample data"""
    with app.app_context():
        db = get_db()
        
        # Create users table
        db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                role TEXT DEFAULT 'guest',
                is_active BOOLEAN DEFAULT 1,
                email_verified BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        ''')
        
        # Create password reset tokens table
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
        
        # Create index for performance
        db.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)')
        db.execute('CREATE INDEX IF NOT EXISTS idx_tokens_token ON password_reset_tokens(token)')
        db.execute('CREATE INDEX IF NOT EXISTS idx_tokens_expires ON password_reset_tokens(expires_at)')
        
        # Check if we have any users, if not, create sample data
        cursor = db.execute('SELECT COUNT(*) FROM users')
        user_count = cursor.fetchone()[0]
        
        if user_count == 0:
            # Create sample users
            sample_users = [
                {
                    'email': 'admin@videotracking.com',
                    'password': bcrypt.hashpw('AdminPass123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
                    'first_name': 'Admin',
                    'last_name': 'User',
                    'role': 'admin'
                },
                {
                    'email': 'test@example.com', 
                    'password': bcrypt.hashpw('TestPass123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
                    'first_name': 'Test',
                    'last_name': 'User',
                    'role': 'guest'
                },
                {
                    'email': 'johnsontakashi45@gmail.com',
                    'password': bcrypt.hashpw('MyPassword123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
                    'first_name': 'Johnson',
                    'last_name': 'Takashi',
                    'role': 'guest'
                }
            ]
            
            for user in sample_users:
                db.execute('''
                    INSERT INTO users (email, password, first_name, last_name, role)
                    VALUES (?, ?, ?, ?, ?)
                ''', (user['email'], user['password'], user['first_name'], user['last_name'], user['role']))
        
        db.commit()
        print(f"✅ Database initialized: {DATABASE}")

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
        cursor = db.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        return dict(cursor.fetchone())
    except sqlite3.IntegrityError:
        return None

def update_password(user_id, new_password):
    """Update user password"""
    db = get_db()
    hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    db.execute('UPDATE users SET password = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?', 
               (hashed_password, user_id))
    db.commit()

def create_reset_token(user_id):
    """Create password reset token"""
    db = get_db()
    token = str(uuid.uuid4())
    expires_at = datetime.now() + timedelta(minutes=30)
    
    db.execute('''
        INSERT INTO password_reset_tokens (user_id, token, expires_at)
        VALUES (?, ?, ?)
    ''', (user_id, token, expires_at))
    db.commit()
    
    return token

def validate_reset_token(token):
    """Validate and get user from reset token"""
    db = get_db()
    cursor = db.execute('''
        SELECT prt.*, u.email, u.first_name, u.last_name 
        FROM password_reset_tokens prt
        JOIN users u ON prt.user_id = u.id
        WHERE prt.token = ? AND prt.expires_at > CURRENT_TIMESTAMP AND prt.used = 0
    ''', (token,))
    
    row = cursor.fetchone()
    if row:
        return dict(row)
    return None

def mark_token_used(token):
    """Mark reset token as used"""
    db = get_db()
    db.execute('UPDATE password_reset_tokens SET used = 1 WHERE token = ?', (token,))
    db.commit()

def cleanup_expired_tokens():
    """Remove expired tokens"""
    db = get_db()
    db.execute('DELETE FROM password_reset_tokens WHERE expires_at < CURRENT_TIMESTAMP')
    db.commit()

# Email service
class EmailService:
    def __init__(self):
        self.sg = None
        if SENDGRID_API_KEY and SENDGRID_API_KEY != 'your-sendgrid-api-key-here':
            try:
                self.sg = SendGridAPIClient(api_key=SENDGRID_API_KEY)
            except Exception as e:
                logger.error(f"Failed to initialize SendGrid: {e}")

    def send_password_reset_email(self, to_email, reset_token, user_name):
        """Send password reset email"""
        if not self.sg:
            logger.warning(f"SendGrid not configured. Would send reset email to {to_email}")
            logger.info(f"Reset URL would be: {FRONTEND_URL}/reset-password?token={reset_token}")
            return True

        reset_url = f"{FRONTEND_URL}/reset-password?token={reset_token}"
        
        subject = "POLITIKOS - Redefinir Senha"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                .email-container {{
                    max-width: 600px;
                    margin: 0 auto;
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: linear-gradient(135deg, #0000cc 0%, #00cc6c 50%, #ffd93d 100%);
                    padding: 2px;
                }}
                .email-content {{
                    background: white;
                    padding: 40px;
                    border-radius: 8px;
                    margin: 2px;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                }}
                .logo {{
                    font-size: 32px;
                    font-weight: bold;
                    background: linear-gradient(135deg, #0000cc, #00cc6c, #ffd93d);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    background-clip: text;
                }}
                .reset-button {{
                    display: inline-block;
                    padding: 12px 30px;
                    background: linear-gradient(135deg, #0000cc, #00cc6c);
                    color: white;
                    text-decoration: none;
                    border-radius: 6px;
                    font-weight: bold;
                    margin: 20px 0;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 30px;
                    color: #666;
                    font-size: 14px;
                }}
            </style>
        </head>
        <body>
            <div class="email-container">
                <div class="email-content">
                    <div class="header">
                        <div class="logo">POLITIKOS</div>
                        <p>Plataforma de Análise Política</p>
                    </div>
                    
                    <h2>Olá, {user_name}!</h2>
                    
                    <p>Você solicitou a redefinição da sua senha. Clique no botão abaixo para criar uma nova senha:</p>
                    
                    <div style="text-align: center;">
                        <a href="{reset_url}" class="reset-button">Redefinir Senha</a>
                    </div>
                    
                    <p><strong>Importante:</strong> Este link é válido por apenas 30 minutos.</p>
                    
                    <p>Se você não solicitou esta redefinição, ignore este email. Sua conta permanecerá segura.</p>
                    
                    <div class="footer">
                        <p>POLITIKOS - Análise Política Avançada<br>
                        Este é um email automático, não responda.</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        POLITIKOS - Redefinir Senha
        
        Olá, {user_name}!
        
        Você solicitou a redefinição da sua senha. 
        
        Acesse o link abaixo para criar uma nova senha:
        {reset_url}
        
        IMPORTANTE: Este link é válido por apenas 30 minutos.
        
        Se você não solicitou esta redefinição, ignore este email. 
        Sua conta permanecerá segura.
        
        POLITIKOS - Análise Política Avançada
        Este é um email automático, não responda.
        """

        try:
            message = Mail(
                from_email=Email(FROM_EMAIL, "POLITIKOS"),
                to_emails=To(to_email),
                subject=subject,
                html_content=Content("text/html", html_content),
                plain_text_content=Content("text/plain", text_content)
            )

            response = self.sg.send(message)
            logger.info(f"Password reset email sent to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send password reset email to {to_email}: {e}")
            return False

email_service = EmailService()

# API Routes
@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        remember_me = data.get('remember_me', False)

        if not email or not password:
            return jsonify({
                'success': False,
                'message': 'Email e senha são obrigatórios'
            }), 400

        user = find_user_by_email(email)
        if not user:
            return jsonify({
                'success': False,
                'message': 'Email ou senha incorretos'
            }), 401

        # Verify password
        if not bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            return jsonify({
                'success': False,
                'message': 'Email ou senha incorretos'
            }), 401

        if not user['is_active']:
            return jsonify({
                'success': False,
                'message': 'Conta desativada. Entre em contato com o suporte'
            }), 401

        # Update last login
        db = get_db()
        db.execute('UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?', (user['id'],))
        db.commit()

        # Create response
        user_response = {
            'id': user['id'],
            'email': user['email'],
            'first_name': user['first_name'],
            'last_name': user['last_name'],
            'full_name': f"{user['first_name']} {user['last_name']}",
            'role': user['role'],
            'is_active': bool(user['is_active']),
            'email_verified': bool(user['email_verified'])
        }

        if user['last_login']:
            user_response['last_login'] = user['last_login']

        return jsonify({
            'success': True,
            'access_token': f"jwt_token_{user['id']}_{secrets.token_hex(8)}",
            'refresh_token': f"refresh_token_{user['id']}_{secrets.token_hex(8)}",
            'token_type': 'Bearer',
            'expires_in': 3600 if remember_me else 900,
            'user': user_response
        })

    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({
            'success': False,
            'message': 'Erro interno do servidor'
        }), 500

@app.route('/api/auth/signup', methods=['POST'])
def signup():
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
        role = data.get('role', 'guest')

        # Validation
        if not email or not password or not first_name or not last_name:
            return jsonify({
                'success': False,
                'message': 'Todos os campos são obrigatórios'
            }), 400

        if len(password) < 8:
            return jsonify({
                'success': False,
                'message': 'Senha deve ter pelo menos 8 caracteres'
            }), 400

        # Check if user already exists
        if find_user_by_email(email):
            return jsonify({
                'success': False,
                'message': 'Email já está em uso'
            }), 409

        # Create user
        user = create_user(email, password, first_name, last_name, role)
        if not user:
            return jsonify({
                'success': False,
                'message': 'Erro ao criar conta'
            }), 500

        return jsonify({
            'success': True,
            'message': 'Conta criada com sucesso! Faça login para continuar',
            'user': {
                'id': user['id'],
                'email': user['email'],
                'first_name': user['first_name'],
                'last_name': user['last_name'],
                'role': user['role']
            }
        })

    except Exception as e:
        logger.error(f"Signup error: {e}")
        return jsonify({
            'success': False,
            'message': 'Erro interno do servidor'
        }), 500

@app.route('/api/auth/request-password-reset', methods=['POST'])
def request_password_reset():
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()

        if not email:
            return jsonify({
                'success': False,
                'message': 'Email é obrigatório'
            }), 400

        user = find_user_by_email(email)
        
        # Always return success for security (prevent email enumeration)
        response_message = "Se o email existir, as instruções de redefinição foram enviadas"
        
        if user and user['is_active']:
            # Clean up old tokens
            cleanup_expired_tokens()
            
            # Generate reset token
            reset_token = create_reset_token(user['id'])
            
            # Send email
            user_name = user['first_name']
            email_sent = email_service.send_password_reset_email(email, reset_token, user_name)
            
            if not email_sent:
                logger.error(f"Failed to send email to {email}")

        return jsonify({
            'success': True,
            'message': response_message
        })

    except Exception as e:
        logger.error(f"Password reset request error: {e}")
        return jsonify({
            'success': False,
            'message': 'Erro interno do servidor'
        }), 500

@app.route('/api/auth/validate-reset-token', methods=['POST'])
def validate_token():
    try:
        data = request.get_json()
        token = data.get('token', '').strip()

        if not token:
            return jsonify({
                'success': False,
                'message': 'Token é obrigatório'
            }), 400

        token_data = validate_reset_token(token)
        
        if not token_data:
            return jsonify({
                'success': False,
                'message': 'Token inválido ou expirado'
            }), 400

        return jsonify({
            'success': True,
            'message': 'Token válido',
            'user_email': token_data['email']
        })

    except Exception as e:
        logger.error(f"Token validation error: {e}")
        return jsonify({
            'success': False,
            'message': 'Erro interno do servidor'
        }), 500

@app.route('/api/auth/reset-password', methods=['POST'])
def reset_password():
    try:
        data = request.get_json()
        token = data.get('token', '').strip()
        new_password = data.get('new_password', '')

        if not token or not new_password:
            return jsonify({
                'success': False,
                'message': 'Token e nova senha são obrigatórios'
            }), 400

        if len(new_password) < 8:
            return jsonify({
                'success': False,
                'message': 'Senha deve ter pelo menos 8 caracteres'
            }), 400

        token_data = validate_reset_token(token)
        
        if not token_data:
            return jsonify({
                'success': False,
                'message': 'Token inválido ou expirado'
            }), 400

        # Update password
        update_password(token_data['user_id'], new_password)
        
        # Mark token as used
        mark_token_used(token)

        return jsonify({
            'success': True,
            'message': 'Senha atualizada com sucesso'
        })

    except Exception as e:
        logger.error(f"Password reset error: {e}")
        return jsonify({
            'success': False,
            'message': 'Erro interno do servidor'
        }), 500

@app.route('/api/auth/me', methods=['GET'])
def get_current_user():
    # Mock endpoint - in production, validate JWT token
    return jsonify({
        'success': True,
        'user': {
            'id': 1,
            'email': 'user@example.com',
            'first_name': 'User',
            'last_name': 'Example',
            'role': 'guest'
        }
    })

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    return jsonify({'success': True, 'message': 'Logout realizado com sucesso'})

@app.route('/api/auth/refresh', methods=['POST'])
def refresh_token():
    return jsonify({
        'success': True,
        'access_token': f"new_jwt_token_{secrets.token_hex(8)}",
        'expires_in': 900
    })

@app.route('/', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'message': 'POLITIKOS API is running',
        'version': '1.0.0'
    })

if __name__ == '__main__':
    print("🚀 Starting POLITIKOS Flask server with persistent database...")
    
    # Initialize database
    init_db()
    
    print("📧 Sample users:")
    print("   - admin@videotracking.com / AdminPass123")
    print("   - test@example.com / TestPass123") 
    print("   - johnsontakashi45@gmail.com / MyPassword123")
    print("🌐 Frontend: http://localhost:3000")
    print("🔧 Backend: http://localhost:5000")
    print("📬 Email service: SendGrid")
    print()
    print("⚙️  Configuration:")
    print(f"   - SENDGRID_API_KEY: {'✅ Set' if SENDGRID_API_KEY and SENDGRID_API_KEY != 'your-sendgrid-api-key-here' else '❌ Not set'}")
    print(f"   - FROM_EMAIL: {FROM_EMAIL}")
    print(f"   - FRONTEND_URL: {FRONTEND_URL}")
    print(f"   - DATABASE: {DATABASE}")
    
    app.run(debug=True, host='0.0.0.0', port=5000)