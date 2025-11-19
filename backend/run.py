import os
from app import create_app, db
from app.models import User, UserRole, RefreshToken, PasswordResetToken, UserSession
from flask_migrate import upgrade

# Create Flask app
app = create_app(os.getenv('FLASK_ENV', 'development'))

@app.cli.command()
def init_db():
    """Initialize database with tables and sample data."""
    print("Creating database tables...")
    db.create_all()
    print("Database tables created successfully!")
    
    # Create sample admin user
    admin = User.query.filter_by(email='admin@videotacking.com').first()
    if not admin:
        admin = User(
            email='admin@videotracking.com',
            password='AdminPass123!',
            first_name='System',
            last_name='Administrator',
            role=UserRole.ADMIN
        )
        admin.email_verified = True
        db.session.add(admin)
        
        # Create sample analyst
        analyst = User(
            email='analyst@videotracking.com',
            password='AnalystPass123!',
            first_name='Data',
            last_name='Analyst',
            role=UserRole.ANALYST
        )
        analyst.email_verified = True
        db.session.add(analyst)
        
        # Create sample guest
        guest = User(
            email='guest@videotracking.com',
            password='GuestPass123!',
            first_name='Guest',
            last_name='User',
            role=UserRole.GUEST
        )
        guest.email_verified = True
        db.session.add(guest)
        
        db.session.commit()
        print("Sample users created:")
        print("- Admin: admin@videotracking.com / AdminPass123!")
        print("- Analyst: analyst@videotracking.com / AnalystPass123!")
        print("- Guest: guest@videotracking.com / GuestPass123!")

@app.cli.command()
def create_admin():
    """Create admin user interactively."""
    import getpass
    
    email = input("Enter admin email: ")
    password = getpass.getpass("Enter admin password: ")
    first_name = input("Enter first name: ")
    last_name = input("Enter last name: ")
    
    # Check if user exists
    if User.query.filter_by(email=email.lower()).first():
        print("User with this email already exists!")
        return
    
    admin = User(
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        role=UserRole.ADMIN
    )
    admin.email_verified = True
    
    db.session.add(admin)
    db.session.commit()
    
    print(f"Admin user {email} created successfully!")

@app.shell_context_processor
def make_shell_context():
    """Make database models available in flask shell."""
    return {
        'db': db,
        'User': User,
        'UserRole': UserRole,
        'RefreshToken': RefreshToken,
        'PasswordResetToken': PasswordResetToken,
        'UserSession': UserSession
    }

if __name__ == '__main__':
    with app.app_context():
        # Auto-create tables if they don't exist
        db.create_all()
    
    # Run the application
    app.run(
        debug=app.config.get('DEBUG', False),
        host='0.0.0.0',
        port=int(os.getenv('PORT', 5000))
    )