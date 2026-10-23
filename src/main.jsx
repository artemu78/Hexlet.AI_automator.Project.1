import React, { StrictMode, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  ArrowUpRight,
  ArrowDown,
  MoveUpRight,
  Dumbbell,
  Activity,
  Sparkles,
  MessageCircle,
  Play,
  Plus,
} from "lucide-react";
import ContactFormDialog from "./ContactFormDialog";
import { version } from "../package.json";
import "./styles.css";

console.info(`App version: ${version}`);

// Replace these URLs with local photos when your club assets are ready.
const photos = {
  club: "https://images.unsplash.com/photo-1534438327276-14e5300c3a48?auto=format&fit=crop&w=2000&q=85",
  training:
    "https://images.unsplash.com/photo-1517836357463-d25dfeac3438?auto=format&fit=crop&w=900&q=85",
  balance:
    "https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?auto=format&fit=crop&w=900&q=85",
};

function App() {
  const [formOpen, setFormOpen] = useState(false);

  return (
    <main className="page">
      <section className="hero" aria-labelledby="hero-title">
        <div
          className="hero__media"
          style={{ backgroundImage: `url(${photos.club})` }}
          aria-hidden="true"
        >
          {/* Add public/club-background.mp4 and set VITE_HERO_VIDEO=club-background.mp4 to enable your video. */}
          {import.meta.env.VITE_HERO_VIDEO && (
            <video autoPlay muted loop playsInline poster={photos.club}>
              <source
                src={`${import.meta.env.BASE_URL}${import.meta.env.VITE_HERO_VIDEO}`}
                type="video/mp4"
              />
            </video>
          )}
        </div>
        <header className="header">
          <div className="brand" aria-label="Импульс фитнес-клуб">
            <Activity aria-hidden="true" />
            <span>
              импульс<span className="brand__dot">.</span>
            </span>
          </div>
          <nav className="nav" aria-label="Главное меню">
            <button type="button">О клубе</button>
            <button type="button">Направления</button>
            <button type="button">Клубные карты</button>
          </nav>
          <button
            type="button"
            className="fitness-button fitness-button--small"
            onClick={() => setFormOpen(true)}
          >
            Написать нам <ArrowUpRight size={18} />
          </button>
        </header>
        <div className="hero__content">
          <div className="eyebrow">
            <span className="live-dot" /> ТВОЯ ЭНЕРГИЯ. ТВОЁ МЕСТО.
          </div>
          <h1 id="hero-title">
            БОЛЬШЕ
            <br />
            ЧЕМ{" "}
            <span>
              ФИТНЕС<span className="title-dot">.</span>
            </span>
          </h1>
          <div className="hero__bottom">
            <p>
              Становись сильнее. Находи баланс.
              <br />
              Почувствуй свой новый ритм жизни.
            </p>
            <button type="button" className="fitness-button">
              Почувствовать импульс <ArrowUpRight size={22} />
            </button>
          </div>
        </div>
        <div className="hero__footer">
          <span>
            <span className="live-dot" /> ДВИЖЕНИЕ НАЧИНАЕТСЯ С ТЕБЯ
          </span>
          <button type="button" className="film-button">
            <Play size={13} fill="currentColor" /> АТМОСФЕРА КЛУБА
          </button>
          <ArrowDown size={20} />
        </div>
        <span className="hero__side">СИЛА ВНУТРИ / IMPULSE FITNESS CLUB</span>
      </section>

      <div className="ticker" aria-hidden="true">
        <span>ТВОЙ РИТМ</span>
        <Plus />
        <span>ТВОЯ СИЛА</span>
        <Plus />
        <span>ТВОЙ ИМПУЛЬС</span>
        <Plus />
        <span>ТВОЙ РИТМ</span>
        <Plus />
      </div>

      <section className="directions" aria-labelledby="directions-title">
        <div className="section-top">
          <span className="eyebrow">01 / НАЙДИ СВОЁ ДВИЖЕНИЕ</span>
          <span className="section-note">
            Разные направления. Одна энергия.
          </span>
        </div>
        <div className="section-heading">
          <h2 id="directions-title">
            В твоём <em>ритме.</em>
          </h2>
          <p>
            Неважно, с чего ты начинаешь.
            <br />
            Важно, что ты делаешь это для себя.
          </p>
        </div>
        <div className="cards">
          <article className="fitness-card fitness-card--strength">
            <img
              src={photos.club}
              alt="Просторный тренажёрный зал с гантелями"
              loading="lazy"
              onError={(event) => {
                event.currentTarget.style.display = "none";
              }}
            />
            <div className="card-top">
              <Dumbbell />
              <span>01</span>
            </div>
            <div className="card-bottom">
              <span>СТАНОВИСЬ СИЛЬНЕЕ</span>
              <h3>Сила и характер</h3>
              <p>Тренажёрный зал</p>
            </div>
            <button
              className="card-button"
              type="button"
              aria-label="Подробнее о тренажёрном зале"
            >
              <MoveUpRight />
            </button>
          </article>
          <article className="fitness-card">
            <img
              src={photos.training}
              alt="Силовая тренировка в фитнес-клубе"
              loading="lazy"
              onError={(event) => {
                event.currentTarget.style.display = "none";
              }}
            />
            <div className="card-top">
              <Activity />
              <span>02</span>
            </div>
            <div className="card-bottom">
              <span>ЗАРЯЖАЙСЯ ЭНЕРГИЕЙ</span>
              <h3>Вместе мощнее</h3>
              <p>Групповые тренировки</p>
            </div>
            <button
              className="card-button"
              type="button"
              aria-label="Подробнее о групповых тренировках"
            >
              <MoveUpRight />
            </button>
          </article>
          <article className="fitness-card">
            <img
              src={photos.balance}
              alt="Занятие йогой на свежем воздухе"
              loading="lazy"
              onError={(event) => {
                event.currentTarget.style.display = "none";
              }}
            />
            <div className="card-top">
              <Sparkles />
              <span>03</span>
            </div>
            <div className="card-bottom">
              <span>ПОЧУВСТВУЙ БАЛАНС</span>
              <h3>Тело и разум</h3>
              <p>Йога и растяжка</p>
            </div>
            <button
              className="card-button"
              type="button"
              aria-label="Подробнее о йоге и растяжке"
            >
              <MoveUpRight />
            </button>
          </article>
        </div>
      </section>
      <section className="closing">
        <div>
          <span className="eyebrow">ПЕРВЫЙ ШАГ — ПРОСТО НАЧАТЬ</span>
          <h2>
            Твой импульс
            <br />
            начинается <em>здесь.</em>
          </h2>
        </div>
        <div className="closing__action">
          <p>
            Есть вопросы? Давай знакомиться.
            <br />
            Поможем найти твоё направление.
          </p>
          <button
            type="button"
            className="fitness-button"
            onClick={() => setFormOpen(true)}
          >
            <MessageCircle size={20} /> Написать нам <ArrowUpRight size={22} />
          </button>
        </div>
      </section>
      <footer className="footer">
        <div className="brand">
          <Activity />
          <span>импульс.</span>
        </div>
        <span>ТВОЁ МЕСТО СТАТЬ СИЛЬНЕЕ</span>
        <span>© {new Date().getFullYear()} Импульс</span>
      </footer>

      <ContactFormDialog open={formOpen} onClose={() => setFormOpen(false)} />
    </main>
  );
}

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <App />
  </StrictMode>,
);

// With defer enabled, send the initial SPA page view explicitly, once per load.
window.ym?.(113655208, "hit", window.location.href, {
  title: document.title,
  referer: document.referrer,
});
