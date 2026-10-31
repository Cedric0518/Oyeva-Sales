import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { apiMode, createApiClient } from './api';
import { App } from './App';
import './styles/global.css';

const root = document.getElementById('root');
if (!root) throw new Error('Missing #root element in index.html.');

const mode = apiMode();

createRoot(root).render(
  <StrictMode>
    <App client={createApiClient(mode)} mockBackend={mode === 'mock'} />
  </StrictMode>,
);
