import React, { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';

function App() {
  return (
    <main className="page">
      <section className="greeting" aria-labelledby="greeting-title">
        <span className="greeting__eyebrow">Your React app is ready</span>
        <h1 id="greeting-title">Hello, world!</h1>
        <p>A small beginning to something great.</p>
      </section>
    </main>
  );
}

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
