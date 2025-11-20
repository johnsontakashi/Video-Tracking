from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins=['http://localhost:3000', 'http://localhost:3001'])

# Temporary in-memory storage for demo
users = [
    {
        'id': 1, 
        'email': 'admin@videotracking.com', 
        'password': 'AdminPass123',
        'first_name': 'Admin',
        'last_name': 'User',
        'role': 'admin'
    },
    {
        'id': 2, 
        'email': 'test@example.com', 
        'password': 'TestPass123',
        'first_name': 'Test',
        'last_name': 'User',
        'role': 'guest'
    }
]

@app.route('/api/hello', methods=['GET'])
def hello():
    return jsonify({'message': 'Hello World from Flask!'})

@app.route('/api/auth/signup', methods=['POST'])
def signup():
    try:
        # Handle JSON parsing more robustly
        data = request.get_json(force=True)
        if not data:
            data = request.json
        
        # Basic validation
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({
                'success': False,
                'error': 'validation_error',
                'message': 'Email and password are required'
            }), 400
        
        # Check if user exists
        for user in users:
            if user['email'].lower() == data['email'].lower():
                return jsonify({
                    'success': False,
                    'error': 'user_exists',
                    'message': 'User with this email already exists'
                }), 400
        
        # Create new user
        new_user = {
            'id': len(users) + 1,
            'email': data['email'].lower(),
            'password': data['password'],  # In real app, this would be hashed
            'first_name': data.get('first_name', ''),
            'last_name': data.get('last_name', ''),
            'role': data.get('role', 'guest')
        }
        users.append(new_user)
        
        # Return user info (without password)
        user_response = {k: v for k, v in new_user.items() if k != 'password'}
        
        return jsonify({
            'success': True,
            'message': 'User registered successfully',
            'user': user_response
        }), 201
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': 'Registration failed'
        }), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        # Handle JSON parsing more robustly
        try:
            data = request.get_json()
        except Exception as json_error:
            print(f"JSON parsing error: {str(json_error)}")
            print(f"Raw data: {request.data}")
            # Try alternative parsing
            import json
            try:
                data = json.loads(request.data.decode('utf-8'))
            except Exception as alt_error:
                print(f"Alternative parsing error: {str(alt_error)}")
                return jsonify({
                    'success': False,
                    'error': 'json_parse_error',
                    'message': 'Could not parse JSON request'
                }), 400
        
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({
                'success': False,
                'error': 'validation_error',
                'message': 'Email and password are required'
            }), 400
        
        # Find user
        user = None
        for u in users:
            if u['email'].lower() == data['email'].lower():
                user = u
                break
        
        if not user or user['password'] != data['password']:
            return jsonify({
                'success': False,
                'error': 'authentication_failed',
                'message': 'Invalid email or password'
            }), 401
        
        # Return mock tokens and user info
        user_response = {k: v for k, v in user.items() if k != 'password'}
        user_response['full_name'] = f"{user['first_name']} {user['last_name']}"
        user_response['is_active'] = True
        user_response['email_verified'] = True
        
        return jsonify({
            'success': True,
            'access_token': 'mock_access_token_' + str(user['id']),
            'refresh_token': 'mock_refresh_token_' + str(user['id']),
            'token_type': 'Bearer',
            'expires_in': 900,
            'user': user_response
        }), 200
        
    except Exception as e:
        print(f"Login error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': f'Login failed: {str(e)}'
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
        
        # Check if email exists (for demo purposes)
        user_exists = False
        for user in users:
            if user['email'].lower() == data['email'].lower():
                user_exists = True
                break
        
        # Always return success for security (don't reveal if email exists)
        # In a real app, you would send an email if the user exists
        if user_exists:
            print(f"📧 Password reset requested for: {data['email']}")
            print(f"🔗 Reset link would be sent to user's email")
        
        return jsonify({
            'success': True,
            'message': 'If the email exists, password reset instructions have been sent'
        }), 200
        
    except Exception as e:
        print(f"Password reset error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': 'Password reset request failed'
        }), 500

if __name__ == '__main__':
    print("🚀 Starting simple Flask server...")
    print("📧 Sample users:")
    print("   - admin@videotracking.com / AdminPass123")
    print("   - test@example.com / TestPass123")
    print("🌐 Frontend: http://localhost:3000")
    print("🔧 Backend: http://localhost:5000")
    
    app.run(debug=True, host='0.0.0.0', port=5000)