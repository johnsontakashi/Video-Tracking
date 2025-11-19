# Legacy app.py - kept for backward compatibility
# Use run.py for the new authentication system

from run import app

# Keep the original celery tasks for backward compatibility
from celery import Celery
from flask import jsonify
import os

def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL']
    )
    celery.conf.update(app.config)
    
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery.Task = ContextTask
    return celery

celery = make_celery(app)

@celery.task
def hello_task(name):
    return f"Hello {name} from Celery!"

# Legacy routes moved to main.py
# New endpoints available at /api/auth/* and /api/*

if __name__ == '__main__':
    # Redirect to run.py
    print("Please use 'python run.py' to start the application with authentication features")
    import sys
    sys.exit(1)