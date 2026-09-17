import { StrictMode } from 'react';
import { hydrateRoot, createRoot } from 'react-dom/client';
import './styles/globals.css';
import './styles/components.css';
import App from './App.tsx';

const rootElement = document.getElementById('root')!;

if (rootElement.hasChildNodes()) {
  hydrateRoot(
    rootElement,
    <StrictMode>
      <App />
    </StrictMode>,
  );
} else {
  createRoot(rootElement).render(
    <StrictMode>
      <App />
    </StrictMode>,
  );
}
