#!/usr/bin/env python3
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)

# Configure CORS to allow requests from frontend
CORS(app, 
     origins=['http://localhost:3000', 'http://localhost:3001', 'http://localhost:3003'],
     allow_headers=['Content-Type', 'Authorization'],
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
     supports_credentials=True)

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'message': 'Test server is running',
        'cors': 'enabled'
    })

@app.route('/api/auth/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS':
        # Handle preflight request
        response = jsonify({'message': 'OK'})
        response.headers.add('Access-Control-Allow-Origin', request.headers.get('Origin', '*'))
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
        return response
    
    data = request.get_json() or {}
    email = data.get('email', '')
    password = data.get('password', '')
    
    # Mock authentication - define test users with different roles
    test_users = {
        'admin@videotracking.com': {
            'id': 1,
            'first_name': 'Admin',
            'last_name': 'User',
            'role': 'admin',
            'email_verified': True
        },
        'analyst@videotracking.com': {
            'id': 2,
            'first_name': 'Data',
            'last_name': 'Analyst',
            'role': 'analyst',
            'email_verified': True
        },
        'guest@videotracking.com': {
            'id': 3,
            'first_name': 'Guest',
            'last_name': 'User',
            'role': 'guest',
            'email_verified': False
        },
        'test@test.com': {
            'id': 4,
            'first_name': 'Test',
            'last_name': 'User',
            'role': 'guest',
            'email_verified': True
        }
    }
    
    if email in test_users and password:
        user_data = test_users[email]
        return jsonify({
            'success': True,
            'access_token': 'mock_access_token_12345',
            'refresh_token': 'mock_refresh_token_67890',
            'token_type': 'Bearer',
            'expires_in': 900,
            'user': {
                **user_data,
                'email': email,
                'full_name': f"{user_data['first_name']} {user_data['last_name']}"
            }
        })
    else:
        return jsonify({
            'success': False,
            'error': 'invalid_credentials',
            'message': 'Invalid email or password'
        }), 401

@app.route('/api/auth/me', methods=['GET', 'OPTIONS'])
def get_current_user():
    if request.method == 'OPTIONS':
        # Handle preflight request
        response = jsonify({'message': 'OK'})
        response.headers.add('Access-Control-Allow-Origin', request.headers.get('Origin', '*'))
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
        return response
    
    # Check for Authorization header
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        # Mock user data for any valid token
        return jsonify({
            'success': True,
            'user': {
                'id': 1,
                'email': 'admin@videotracking.com',
                'first_name': 'Admin',
                'last_name': 'User',
                'role': 'admin',
                'email_verified': True
            }
        })
    else:
        return jsonify({
            'success': False,
            'error': 'unauthorized',
            'message': 'Authentication required'
        }), 401

@app.route('/api/auth/logout', methods=['POST', 'OPTIONS'])
def logout():
    if request.method == 'OPTIONS':
        # Handle preflight request
        response = jsonify({'message': 'OK'})
        response.headers.add('Access-Control-Allow-Origin', request.headers.get('Origin', '*'))
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
        return response
    
    # Mock logout - always successful
    return jsonify({
        'success': True,
        'message': 'Logged out successfully'
    })

@app.route('/api/payment/plans', methods=['GET'])
def get_plans():
    return jsonify({
        'plans': [
            {
                'id': 1,
                'plan_type': 'starter',
                'name': 'Basic',
                'price': 29,
                'influencer_limit': 100,
                'posts_per_month': 1000,
                'analytics_retention_days': 90,
                'features': ['basic_analytics', 'manual_tracking'],
                'is_active': True
            },
            {
                'id': 2,
                'plan_type': 'professional',
                'name': 'Professional', 
                'price': 99,
                'influencer_limit': 1000,
                'posts_per_month': 10000,
                'analytics_retention_days': 365,
                'features': ['advanced_analytics', 'automated_tracking', 'sentiment_analysis'],
                'is_active': True
            },
            {
                'id': 3,
                'plan_type': 'enterprise',
                'name': 'Enterprise',
                'price': 299,
                'influencer_limit': -1,
                'posts_per_month': -1,
                'analytics_retention_days': -1,
                'features': ['enterprise_analytics', 'api_access', 'white_label', 'dedicated_support'],
                'is_active': True
            }
        ]
    })

@app.route('/api/analytics/dashboard', methods=['GET'])
def get_analytics_dashboard():
    return jsonify({
        'summary': {
            'total_influencers': 1247,
            'total_posts': 8456,
            'total_engagement': 342567,
            'avg_engagement_rate': 4.2,
            'top_platforms': [
                {'platform': 'Instagram', 'count': 520},
                {'platform': 'YouTube', 'count': 340},
                {'platform': 'TikTok', 'count': 287},
                {'platform': 'Twitter', 'count': 100}
            ],
            'engagement_trend': [
                {'date': '2024-01-01', 'engagement': 12450},
                {'date': '2024-01-02', 'engagement': 13200},
                {'date': '2024-01-03', 'engagement': 11800},
                {'date': '2024-01-04', 'engagement': 14600},
                {'date': '2024-01-05', 'engagement': 15100},
                {'date': '2024-01-06', 'engagement': 13900},
                {'date': '2024-01-07', 'engagement': 16200}
            ]
        }
    })

@app.route('/api/collection/influencers', methods=['GET'])
def get_influencers():
    return jsonify({
        'influencers': [
            {
                'id': 1,
                'external_id': 'techguru123',
                'username': 'techguru123',
                'display_name': 'Tech Guru',
                'platform': 'instagram',
                'bio': 'Technology enthusiast sharing the latest trends',
                'verified': True,
                'follower_count': 125000,
                'following_count': 1200,
                'post_count': 245,
                'engagement_rate': 4.2,
                'status': 'active',
                'created_at': '2024-01-15T10:30:00Z'
            },
            {
                'id': 2,
                'external_id': 'fashionista_rio',
                'username': 'fashionista_rio', 
                'display_name': 'Fashion Rio',
                'platform': 'instagram',
                'bio': 'Fashion influencer from Rio de Janeiro',
                'verified': False,
                'follower_count': 89000,
                'following_count': 850,
                'post_count': 189,
                'engagement_rate': 3.8,
                'status': 'active',
                'created_at': '2024-01-20T14:15:00Z'
            }
        ]
    })

@app.route('/api/users', methods=['GET'])
def get_users():
    return jsonify({
        'users': [
            {'id': 1, 'email': 'admin@videotracking.com', 'first_name': 'Admin', 'last_name': 'User', 'role': 'admin', 'status': 'active'},
            {'id': 2, 'email': 'analyst@company.com', 'first_name': 'Data', 'last_name': 'Analyst', 'role': 'analyst', 'status': 'active'},
            {'id': 3, 'email': 'guest@example.com', 'first_name': 'Guest', 'last_name': 'User', 'role': 'guest', 'status': 'active'}
        ]
    })

@app.route('/api/users', methods=['POST', 'OPTIONS'])
def create_user():
    if request.method == 'OPTIONS':
        # Handle preflight request
        response = jsonify({'message': 'OK'})
        response.headers.add('Access-Control-Allow-Origin', request.headers.get('Origin', '*'))
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
        return response
    
    data = request.get_json() or {}
    
    # Mock user creation - simulate success
    new_user = {
        'id': 999,  # Mock ID
        'email': data.get('email'),
        'first_name': data.get('first_name'),
        'last_name': data.get('last_name'),
        'full_name': f"{data.get('first_name', '')} {data.get('last_name', '')}",
        'username': data.get('username'),
        'role': data.get('role', 'guest'),
        'is_active': data.get('is_active', True),
        'email_verified': False,
        'current_plan': 'free',
        'created_at': '2024-01-21T00:00:00Z'
    }
    
    return jsonify({
        'success': True,
        'message': 'User created successfully',
        'user': new_user
    })

@app.route('/api/users/<int:user_id>', methods=['PUT', 'OPTIONS'])
def update_user(user_id):
    if request.method == 'OPTIONS':
        # Handle preflight request
        response = jsonify({'message': 'OK'})
        response.headers.add('Access-Control-Allow-Origin', request.headers.get('Origin', '*'))
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
        return response
    
    data = request.get_json() or {}
    
    # Mock user update - simulate success
    updated_user = {
        'id': user_id,
        'email': data.get('email'),
        'first_name': data.get('first_name'),
        'last_name': data.get('last_name'),
        'full_name': f"{data.get('first_name', '')} {data.get('last_name', '')}",
        'username': data.get('username'),
        'role': data.get('role', 'guest'),
        'is_active': data.get('is_active', True),
        'email_verified': True,
        'current_plan': 'free',
        'created_at': '2024-01-15T00:00:00Z'
    }
    
    return jsonify({
        'success': True,
        'message': 'User updated successfully',
        'user': updated_user
    })

if __name__ == '__main__':
    print("Starting test server with CORS enabled...")
    print("Frontend origins allowed: http://localhost:3000, http://localhost:3001, http://localhost:3003")
    print("\nAvailable test accounts:")
    print("  admin@videotracking.com / any_password (admin role)")
    print("  analyst@videotracking.com / any_password (analyst role)")  
    print("  guest@videotracking.com / any_password (guest role)")
    print("  test@test.com / any_password (guest role)")
    print("")
    app.run(host='0.0.0.0', port=5000, debug=True)