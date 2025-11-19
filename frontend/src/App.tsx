import React, { useState } from 'react';
import './App.css';

interface TaskResponse {
  task_id: string;
  status: string;
}

interface TaskResult {
  state: string;
  result?: string;
  status?: string;
}

function App() {
  const [message, setMessage] = useState<string>('');
  const [taskId, setTaskId] = useState<string>('');
  const [taskResult, setTaskResult] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);

  const fetchHello = async () => {
    try {
      const response = await fetch('http://localhost:5001/api/hello');
      const data = await response.json();
      setMessage(data.message);
    } catch (error) {
      console.error('Error:', error);
      setMessage('Error connecting to backend');
    }
  };

  const startAsyncTask = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:5001/api/hello-async/World', {
        method: 'POST'
      });
      const data: TaskResponse = await response.json();
      setTaskId(data.task_id);
      setTaskResult('Task started...');
      
      // Poll for result
      pollTaskResult(data.task_id);
    } catch (error) {
      console.error('Error:', error);
      setTaskResult('Error starting task');
      setLoading(false);
    }
  };

  const pollTaskResult = async (id: string) => {
    try {
      const response = await fetch(`http://localhost:5001/api/task/${id}`);
      const data: TaskResult = await response.json();
      
      if (data.state === 'SUCCESS') {
        setTaskResult(data.result || 'Task completed');
        setLoading(false);
      } else if (data.state === 'PENDING') {
        setTimeout(() => pollTaskResult(id), 1000);
      } else {
        setTaskResult(data.status || 'Task failed');
        setLoading(false);
      }
    } catch (error) {
      console.error('Error:', error);
      setTaskResult('Error checking task status');
      setLoading(false);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Hello World - React + Flask + Celery + Redis</h1>
        
        <div className="button-container">
          <button onClick={fetchHello}>
            Get Hello from Flask
          </button>
          {message && <p className="message">{message}</p>}
        </div>

        <div className="button-container">
          <button onClick={startAsyncTask} disabled={loading}>
            {loading ? 'Processing...' : 'Start Async Task'}
          </button>
          {taskId && <p className="task-id">Task ID: {taskId}</p>}
          {taskResult && <p className="message">{taskResult}</p>}
        </div>
      </header>
    </div>
  );
}

export default App;
