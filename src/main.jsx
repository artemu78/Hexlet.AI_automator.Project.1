import React, { StrictMode, useState } from 'react';
import { createRoot } from 'react-dom/client';
import ContactFormDialog from './ContactFormDialog';
import './styles.css';

function App() {
  const [formOpen, setFormOpen] = useState(false);

  return (
    <main className="page">
      <section className="greeting" aria-labelledby="greeting-title">
        <span className="greeting__eyebrow">Your React app is ready</span>
        <h1 id="greeting-title">Hello, world!</h1>
        <p>A small beginning to something great.</p>
        <div className="greeting__actions">
          <button type="button" className="button" onClick={() => setFormOpen(true)}>
            Написать нам
          </button>
        </div>
      </section>

      <ContactFormDialog open={formOpen} onClose={() => setFormOpen(false)} />
    </main>
  );
}

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
);

// With defer enabled, send the initial SPA page view explicitly, once per load.
window.ym?.(113655208, 'hit', window.location.href, {
  title: document.title,
  referer: document.referrer,
});
