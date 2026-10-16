import React, { useEffect, useRef, useState } from 'react';

export default function ContactFormDialog({ open, onClose }) {
  const [message, setMessage] = useState('');
  const [contacts, setContacts] = useState('');
  const [error, setError] = useState(null);
  const [sent, setSent] = useState(false);
  const firstFieldRef = useRef(null);

  useEffect(() => {
    if (!open) {
      setMessage('');
      setContacts('');
      setError(null);
      setSent(false);
      return undefined;
    }

    const onKeyDown = (event) => {
      if (event.key === 'Escape') onClose();
    };

    document.addEventListener('keydown', onKeyDown);
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    firstFieldRef.current?.focus();

    return () => {
      document.removeEventListener('keydown', onKeyDown);
      document.body.style.overflow = previousOverflow;
    };
  }, [open, onClose]);

  if (!open) return null;

  const handleSubmit = (event) => {
    event.preventDefault();
    if (!message.trim() || !contacts.trim()) {
      setError('Заполните оба поля.');
      return;
    }
    setError(null);
    setSent(true);
  };

  return (
    <div className="dialog">
      <div className="dialog__overlay" aria-hidden="true" onClick={onClose} />
      <div className="dialog__box" role="dialog" aria-modal="true" aria-labelledby="contact-title">
        <button type="button" className="dialog__close" aria-label="Закрыть" onClick={onClose}>
          ×
        </button>

        <h2 id="contact-title" className="dialog__title">
          Напишите нам
        </h2>
        <p className="dialog__subtitle">Пара строк — и мы свяжемся с вами.</p>

        {sent ? (
          <div className="dialog__done">
            <span className="dialog__done-mark" aria-hidden="true">
              ✓
            </span>
            <p>Сообщение отправлено. Спасибо!</p>
            <button type="button" className="button button--ghost" onClick={onClose}>
              Закрыть
            </button>
          </div>
        ) : (
          <form className="dialog__form" onSubmit={handleSubmit} noValidate>
            <label className="field" htmlFor="contact-message">
              <span className="field__label">Сообщение</span>
              <textarea
                id="contact-message"
                ref={firstFieldRef}
                name="message"
                rows="3"
                placeholder="Коротко о вашем вопросе"
                value={message}
                onChange={(event) => setMessage(event.target.value)}
                aria-invalid={error ? 'true' : undefined}
              />
            </label>

            <label className="field" htmlFor="contact-contacts">
              <span className="field__label">Контакты</span>
              <input
                id="contact-contacts"
                name="contacts"
                type="text"
                autoComplete="off"
                placeholder="e-mail, телефон или @telegram"
                value={contacts}
                onChange={(event) => setContacts(event.target.value)}
                aria-invalid={error ? 'true' : undefined}
              />
            </label>

            {error ? (
              <p className="dialog__error" role="alert">
                {error}
              </p>
            ) : null}

            <button type="submit" className="button dialog__submit">
              Отправить
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
