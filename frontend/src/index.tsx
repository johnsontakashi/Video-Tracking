import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import reportWebVitals from './reportWebVitals';

// Suppress Ant Design React 19 compatibility warnings in development
if (process.env.NODE_ENV === 'development') {
  const originalWarn = console.warn;
  const originalError = console.error;
  
  const shouldSuppressMessage = (message: any) => {
    if (typeof message === 'string') {
      return (
        message.includes('antd v5 support React is 16 ~ 18') ||
        message.includes('[antd: compatible]') ||
        message.includes('antd v5 support React') ||
        message.includes('see https://u.ant.design/v5-for-19')
      );
    }
    return false;
  };
  
  console.warn = (...args) => {
    if (shouldSuppressMessage(args[0])) {
      return; // Suppress Ant Design compatibility warnings
    }
    originalWarn.apply(console, args);
  };
  
  console.error = (...args) => {
    if (shouldSuppressMessage(args[0])) {
      return; // Suppress Ant Design compatibility errors too
    }
    originalError.apply(console, args);
  };
}

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
