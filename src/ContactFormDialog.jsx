import React, { useEffect, useRef, useState } from "react";

import { normalizeContact, sendContact } from "./contact-api.js";

export default function ContactFormDialog({ open, onClose }) {
  const [message, setMessage] = useState("");
  const [contacts, setContacts] = useState("");
  const [error, setError] = useState(null);
  const [sent, setSent] = useState(false);
  const [pending, setPending] = useState(false);
  const [website, setWebsite] = useState("");
  const attempt = useRef(null);
  const busy = useRef(false);
  const firstFieldRef = useRef(null);

  useEffect(() => {
    if (!open) {
      if (busy.current) return undefined;
      attempt.current = null;
      setWebsite("");
      setMessage("");
      setContacts("");
      setError(null);
      setSent(false);
      return undefined;
    }

    const onKeyDown = (event) => {
      if (event.key === "Escape" && !busy.current) onClose();
    };

    document.addEventListener("keydown", onKeyDown);
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    firstFieldRef.current?.focus();

    return () => {
      document.removeEventListener("keydown", onKeyDown);
      document.body.style.overflow = previousOverflow;
    };
  }, [open, onClose]);

  if (!open) return null;

  const close = () => { if (!busy.current) onClose(); };
  const handleSubmit = async (event) => {
    event.preventDefault();
    if (busy.current) return;
    try {
      const values = normalizeContact(message, contacts);
      const fingerprint = JSON.stringify(values);
      if (!attempt.current || attempt.current.fingerprint !== fingerprint) {
        attempt.current = { fingerprint, id: crypto.randomUUID() };
      }
      busy.current = true;
      setPending(true);
      setError(null);
      await sendContact(import.meta.env.VITE_CONTACT_API_URL, {
        id: attempt.current.id, ...values, website,
      });
      setSent(true);
    } catch (error) {
      setError(error.message);
    } finally {
      busy.current = false;
      setPending(false);
    }
  };

  return (
    <div className="dialog">
      <div className="dialog__overlay" aria-hidden="true" onClick={close} />
      <div
        className="dialog__box"
        role="dialog"
        aria-modal="true"
        aria-labelledby="contact-title"
      >
        <button
          type="button"
          disabled={pending}
          className="dialog__close"
          aria-label="Закрыть"
          onClick={close}
        >
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
            <p>Заявка принята</p>
            <button
              type="button"
              className="button button--ghost"
              onClick={close}
            >
              Закрыть
            </button>
          </div>
        ) : (
          <form aria-busy={pending} className="dialog__form" onSubmit={handleSubmit} noValidate>
            <label className="field" htmlFor="contact-message">
              <span className="field__label">Сообщение (до 1000 символов)</span>
              <textarea
                id="contact-message"
                ref={firstFieldRef}
                name="message"
                disabled={pending}
                required
                rows="3"
                placeholder="Коротко о вашем вопросе"
                value={message}
                onChange={(event) => setMessage(event.target.value)}
                aria-invalid={error ? "true" : undefined}
              />
            </label>

            <label className="field" htmlFor="contact-contacts">
              <span className="field__label">Контакты (до 100 символов)</span>
              <input
                id="contact-contacts"
                name="contacts"
                disabled={pending}
                required
                type="text"
                autoComplete="off"
                placeholder="e-mail, телефон или @telegram"
                value={contacts}
                onChange={(event) => setContacts(event.target.value)}
                aria-invalid={error ? "true" : undefined}
              />
            </label>

            <label className="contact-trap" aria-hidden="true">
              Website
              <input name="website" tabIndex={-1} autoComplete="off" value={website}
                onChange={(event) => setWebsite(event.target.value)} />
            </label>

            {error ? (
              <p className="dialog__error" role="alert">
                {error}
              </p>
            ) : null}

            <button
              disabled={pending}
              type="submit"
              className="button dialog__submit"
              onClick={() =>
                window.ym?.(113655208, "reachGoal", "contact_form_submit_click")
              }
            >
              {pending ? "Сохраняем…" : "Отправить"}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
