import os
import secrets
import bcrypt
import uuid
from datetime import datetime, timedelta
from flask import Flask, jsonify, request
from flask_cors import CORS
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
import logging

app = Flask(__name__)
CORS(app, origins=['http://localhost:3000', 'http://localhost:3001'])

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# SendGrid configuration (set your API key as environment variable)
SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY', 'your-sendgrid-api-key-here')
FROM_EMAIL = os.environ.get('FROM_EMAIL', 'noreply@politikos.com')
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:3000')

# In-memory storage for demo (replace with real database in production)
users = [
    {
        'id': 1, 
        'email': 'admin@videotracking.com', 
        'password': bcrypt.hashpw('AdminPass123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
        'first_name': 'Admin',
        'last_name': 'User',
        'role': 'admin'
    },
    {
        'id': 2, 
        'email': 'test@example.com', 
        'password': bcrypt.hashpw('TestPass123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
        'first_name': 'Test',
        'last_name': 'User',
        'role': 'guest'
    },
    {
        'id': 3,
        'email': 'johnsontakashi45@gmail.com',
        'password': bcrypt.hashpw('MyPassword123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
        'first_name': 'Johnson',
        'last_name': 'Takashi',
        'role': 'guest'
    }
]

# Password reset tokens storage (replace with database in production)
password_reset_tokens = {}

class EmailService:
    @staticmethod
    def send_password_reset_email(to_email, reset_token, user_name):
        """Send password reset email using SendGrid"""
        try:
            # Create reset link
            reset_link = f"{FRONTEND_URL}/reset-password?token={reset_token}"
            
            # Create email content
            subject = "POLITIKOS - Redefinir Senha"
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{ font-family: 'Montserrat', Arial, sans-serif; margin: 0; padding: 20px; background-color: #f8f9fa; }}
                    .container {{ max-width: 600px; margin: 0 auto; background-color: white; border-radius: 16px; overflow: hidden; box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15); }}
                    .header {{ background: linear-gradient(135deg, #0000cc 0%, #00cc6c 50%, #ffd93d 100%); padding: 30px; text-align: center; }}
                    .logo {{ color: white; font-size: 28px; font-weight: 700; margin-bottom: 10px; }}
                    .subtitle {{ color: rgba(255,255,255,0.9); font-size: 14px; }}
                    .content {{ padding: 40px 30px; }}
                    .title {{ color: #1a1a1a; font-size: 24px; font-weight: 600; margin-bottom: 20px; }}
                    .message {{ color: #4a4a4a; line-height: 1.6; margin-bottom: 30px; }}
                    .button {{ display: inline-block; background: linear-gradient(135deg, #0000cc 0%, #00cc6c 100%); color: white; text-decoration: none; padding: 14px 28px; border-radius: 12px; font-weight: 600; margin: 20px 0; }}
                    .warning {{ background: #fff3cd; border: 1px solid #ffeaa7; color: #856404; padding: 15px; border-radius: 8px; margin: 20px 0; }}
                    .footer {{ background: #f8f9fa; padding: 20px; text-align: center; color: #757575; font-size: 12px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <div class="logo">POLITIKOS</div>
                        <div class="subtitle">Análise Política Brasileira</div>
                    </div>
                    <div class="content">
                        <h2 class="title">Olá, {user_name}!</h2>
                        <p class="message">
                            Recebemos uma solicitação para redefinir a senha da sua conta POLITIKOS. 
                            Se você fez esta solicitação, clique no botão abaixo para criar uma nova senha:
                        </p>
                        <a href="{reset_link}" class="button">Redefinir Minha Senha</a>
                        <div class="warning">
                            <strong>⚠️ Importante:</strong><br>
                            • Este link expira em 30 minutos por segurança<br>
                            • Se você não solicitou esta redefinição, ignore este email<br>
                            • Nunca compartilhe este link com outras pessoas
                        </div>
                        <p class="message">
                            Se o botão não funcionar, copie e cole este link no seu navegador:<br>
                            <small style="word-break: break-all; color: #0000cc;">{reset_link}</small>
                        </p>
                    </div>
                    <div class="footer">
                        <p>Esta é uma mensagem automática do sistema POLITIKOS.<br>
                        Para dúvidas, entre em contato com nossa equipe de suporte.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Plain text version
            text_content = f"""
            POLITIKOS - Redefinir Senha
            
            Olá, {user_name}!
            
            Recebemos uma solicitação para redefinir a senha da sua conta POLITIKOS.
            Se você fez esta solicitação, acesse o link abaixo para criar uma nova senha:
            
            {reset_link}
            
            IMPORTANTE:
            - Este link expira em 30 minutos por segurança
            - Se você não solicitou esta redefinição, ignore este email
            - Nunca compartilhe este link com outras pessoas
            
            Esta é uma mensagem automática do sistema POLITIKOS.
            """
            
            # Create SendGrid message
            message = Mail(
                from_email=FROM_EMAIL,
                to_emails=to_email,
                subject=subject,
                html_content=html_content,
                plain_text_content=text_content
            )
            
            # Send email
            sg = SendGridAPIClient(api_key=SENDGRID_API_KEY)
            response = sg.send(message)
            
            logger.info(f"Password reset email sent to {to_email}. Status: {response.status_code}")
            return True, None
            
        except Exception as e:
            logger.error(f"Failed to send password reset email to {to_email}: {str(e)}")
            return False, str(e)

class TokenManager:
    @staticmethod
    def generate_reset_token(user_id):
        """Generate a secure password reset token"""
        token = str(uuid.uuid4())
        expiry = datetime.utcnow() + timedelta(minutes=30)
        
        password_reset_tokens[token] = {
            'user_id': user_id,
            'expires_at': expiry,
            'created_at': datetime.utcnow(),
            'used': False
        }
        
        return token
    
    @staticmethod
    def validate_reset_token(token):
        """Validate password reset token"""
        if token not in password_reset_tokens:
            return False, "Token inválido"
        
        token_data = password_reset_tokens[token]
        
        if token_data['used']:
            return False, "Token já foi utilizado"
        
        if datetime.utcnow() > token_data['expires_at']:
            # Clean up expired token
            del password_reset_tokens[token]
            return False, "Token expirado"
        
        return True, token_data
    
    @staticmethod
    def mark_token_as_used(token):
        """Mark token as used"""
        if token in password_reset_tokens:
            password_reset_tokens[token]['used'] = True
    
    @staticmethod
    def cleanup_expired_tokens():
        """Clean up expired tokens"""
        current_time = datetime.utcnow()
        expired_tokens = [
            token for token, data in password_reset_tokens.items()
            if current_time > data['expires_at']
        ]
        
        for token in expired_tokens:
            del password_reset_tokens[token]
        
        return len(expired_tokens)

def find_user_by_email(email):
    """Find user by email address"""
    for user in users:
        if user['email'].lower() == email.lower():
            return user
    return None

def find_user_by_id(user_id):
    """Find user by ID"""
    for user in users:
        if user['id'] == user_id:
            return user
    return None

def validate_password_strength(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Senha deve ter pelo menos 8 caracteres"
    
    if not any(c.isupper() for c in password):
        return False, "Senha deve conter pelo menos uma letra maiúscula"
    
    if not any(c.islower() for c in password):
        return False, "Senha deve conter pelo menos uma letra minúscula"
    
    if not any(c.isdigit() for c in password):
        return False, "Senha deve conter pelo menos um número"
    
    return True, "Senha válida"

# API Routes

@app.route('/api/hello', methods=['GET'])
def hello():
    return jsonify({'message': 'Hello World from Enhanced Flask!'})

@app.route('/api/auth/signup', methods=['POST'])
def signup():
    try:
        data = request.get_json(force=True)
        if not data:
            data = request.json
        
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({
                'success': False,
                'error': 'validation_error',
                'message': 'Email e senha são obrigatórios'
            }), 400
        
        # Check if user exists
        if find_user_by_email(data['email']):
            return jsonify({
                'success': False,
                'error': 'user_exists',
                'message': 'Usuário com este email já existe'
            }), 400
        
        # Validate password strength
        valid, message = validate_password_strength(data['password'])
        if not valid:
            return jsonify({
                'success': False,
                'error': 'password_weak',
                'message': message
            }), 400
        
        # Hash password
        hashed_password = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Create new user
        new_user = {
            'id': max([u['id'] for u in users]) + 1 if users else 1,
            'email': data['email'].lower(),
            'password': hashed_password,
            'first_name': data.get('first_name', ''),
            'last_name': data.get('last_name', ''),
            'role': data.get('role', 'guest')
        }
        users.append(new_user)
        
        # Return user info (without password)
        user_response = {k: v for k, v in new_user.items() if k != 'password'}
        
        return jsonify({
            'success': True,
            'message': 'Usuário registrado com sucesso',
            'user': user_response
        }), 201
        
    except Exception as e:
        logger.error(f"Signup error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': 'Falha no registro'
        }), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({
                'success': False,
                'error': 'validation_error',
                'message': 'Email e senha são obrigatórios'
            }), 400
        
        # Find user
        user = find_user_by_email(data['email'])
        
        if not user:
            return jsonify({
                'success': False,
                'error': 'authentication_failed',
                'message': 'Email ou senha inválidos'
            }), 401
        
        # Verify password
        if not bcrypt.checkpw(data['password'].encode('utf-8'), user['password'].encode('utf-8')):
            return jsonify({
                'success': False,
                'error': 'authentication_failed',
                'message': 'Email ou senha inválidos'
            }), 401
        
        # Return mock tokens and user info
        user_response = {k: v for k, v in user.items() if k != 'password'}
        user_response['full_name'] = f"{user['first_name']} {user['last_name']}"
        user_response['is_active'] = True
        user_response['email_verified'] = True
        
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
            'message': 'Falha no login'
        }), 500

@app.route('/api/auth/me', methods=['GET'])
def get_me():
    # Mock authenticated user response
    return jsonify({
        'success': True,
        'user': {
            'id': 1,
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'full_name': 'Test User',
            'role': 'guest',
            'is_active': True,
            'email_verified': True
        }
    })

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    return jsonify({
        'success': True,
        'message': 'Logout realizado com sucesso'
    })

@app.route('/api/auth/request-password-reset', methods=['POST'])
def request_password_reset():
    try:
        data = request.get_json()
        
        if not data or not data.get('email'):
            return jsonify({
                'success': False,
                'error': 'validation_error',
                'message': 'Email é obrigatório'
            }), 400
        
        # Find user
        user = find_user_by_email(data['email'])
        
        # Always return success for security (don't reveal if email exists)
        if user:
            # Generate reset token
            reset_token = TokenManager.generate_reset_token(user['id'])
            
            # Send email
            success, error = EmailService.send_password_reset_email(
                user['email'], 
                reset_token,
                f"{user['first_name']} {user['last_name']}"
            )
            
            if success:
                logger.info(f"Password reset email sent to {user['email']}")
            else:
                logger.error(f"Failed to send email to {user['email']}: {error}")
        else:
            logger.info(f"Password reset requested for non-existent email: {data['email']}")
        
        return jsonify({
            'success': True,
            'message': 'Se o email existir, as instruções de redefinição foram enviadas'
        }), 200
        
    except Exception as e:
        logger.error(f"Password reset request error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': 'Falha na solicitação de redefinição de senha'
        }), 500

@app.route('/api/auth/reset-password', methods=['POST'])
def reset_password():
    try:
        data = request.get_json()
        
        if not data or not data.get('token') or not data.get('new_password'):
            return jsonify({
                'success': False,
                'error': 'validation_error',
                'message': 'Token e nova senha são obrigatórios'
            }), 400
        
        # Validate token
        valid, token_data_or_error = TokenManager.validate_reset_token(data['token'])
        
        if not valid:
            return jsonify({
                'success': False,
                'error': 'invalid_token',
                'message': token_data_or_error
            }), 400
        
        # Validate new password strength
        valid, message = validate_password_strength(data['new_password'])
        if not valid:
            return jsonify({
                'success': False,
                'error': 'password_weak',
                'message': message
            }), 400
        
        # Find user
        user = find_user_by_id(token_data_or_error['user_id'])
        if not user:
            return jsonify({
                'success': False,
                'error': 'user_not_found',
                'message': 'Usuário não encontrado'
            }), 404
        
        # Hash new password
        new_password_hash = bcrypt.hashpw(data['new_password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Update user password
        user['password'] = new_password_hash
        
        # Mark token as used
        TokenManager.mark_token_as_used(data['token'])
        
        logger.info(f"Password reset successful for user {user['email']}")
        
        return jsonify({
            'success': True,
            'message': 'Senha redefinida com sucesso'
        }), 200
        
    except Exception as e:
        logger.error(f"Password reset error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': 'Falha na redefinição de senha'
        }), 500

@app.route('/api/auth/validate-reset-token', methods=['POST'])
def validate_reset_token():
    """Validate reset token without using it"""
    try:
        data = request.get_json()
        
        if not data or not data.get('token'):
            return jsonify({
                'success': False,
                'error': 'validation_error',
                'message': 'Token é obrigatório'
            }), 400
        
        # Validate token
        valid, token_data_or_error = TokenManager.validate_reset_token(data['token'])
        
        if not valid:
            return jsonify({
                'success': False,
                'error': 'invalid_token',
                'message': token_data_or_error
            }), 400
        
        # Find user
        user = find_user_by_id(token_data_or_error['user_id'])
        if not user:
            return jsonify({
                'success': False,
                'error': 'user_not_found',
                'message': 'Usuário não encontrado'
            }), 404
        
        return jsonify({
            'success': True,
            'message': 'Token válido',
            'user_email': user['email']
        }), 200
        
    except Exception as e:
        logger.error(f"Token validation error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': 'Falha na validação do token'
        }), 500

@app.route('/api/auth/cleanup-tokens', methods=['POST'])
def cleanup_tokens():
    """Admin endpoint to cleanup expired tokens"""
    try:
        cleaned = TokenManager.cleanup_expired_tokens()
        return jsonify({
            'success': True,
            'message': f'{cleaned} tokens expirados removidos'
        }), 200
    except Exception as e:
        logger.error(f"Token cleanup error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': 'Falha na limpeza de tokens'
        }), 500

if __name__ == '__main__':
    print("🚀 Starting enhanced Flask server with email functionality...")
    print("📧 Sample users:")
    print("   - admin@videotracking.com / AdminPass123")
    print("   - test@example.com / TestPass123")
    print("   - johnsontakashi45@gmail.com / MyPassword123")
    print("🌐 Frontend: http://localhost:3000")
    print("🔧 Backend: http://localhost:5000")
    print("📬 Email service: SendGrid")
    print("\n⚙️  Configuration:")
    print(f"   - SENDGRID_API_KEY: {'✅ Set' if SENDGRID_API_KEY != 'your-sendgrid-api-key-here' else '❌ Not set'}")
    print(f"   - FROM_EMAIL: {FROM_EMAIL}")
    print(f"   - FRONTEND_URL: {FRONTEND_URL}")
    
    # Cleanup expired tokens on startup
    TokenManager.cleanup_expired_tokens()
    
    app.run(debug=True, host='0.0.0.0', port=5000)