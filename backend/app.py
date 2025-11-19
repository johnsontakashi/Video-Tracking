from flask import Flask, jsonify
from flask_cors import CORS
from celery import Celery
import os

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['CELERY_BROKER_URL'] = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    app.config['CELERY_RESULT_BACKEND'] = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # Enable CORS for React frontend
    CORS(app, origins=['http://localhost:3001'])
    
    return app

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

app = create_app()
celery = make_celery(app)

@celery.task
def hello_task(name):
    return f"Hello {name} from Celery!"

@app.route('/api/hello', methods=['GET'])
def hello():
    return jsonify({'message': 'Hello World from Flask!'})

@app.route('/api/hello-async/<name>', methods=['POST'])
def hello_async(name):
    task = hello_task.delay(name)
    return jsonify({'task_id': task.id, 'status': 'Task started'})

@app.route('/api/task/<task_id>', methods=['GET'])
def get_task_result(task_id):
    task = hello_task.AsyncResult(task_id)
    if task.state == 'PENDING':
        return jsonify({'state': task.state, 'status': 'Task is waiting...'})
    elif task.state == 'SUCCESS':
        return jsonify({'state': task.state, 'result': task.result})
    else:
        return jsonify({'state': task.state, 'status': str(task.info)})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)