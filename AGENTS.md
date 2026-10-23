# Project guide

Russian-language fitness club SPA built with React, Vite, and Lucide icons. One page, no subpages; promotional buttons are decorative. “Написать нам” opens the contact dialog. The fullscreen hero supports a background video and replaceable fitness photos.

## Documentation

- [README.md](README.md): local setup, build, background video, analytics, and GitHub Pages publishing.
- [CONTEXT.md](CONTEXT.md): domain terminology for contact submissions.
- [docs/contact-api.md](docs/contact-api.md): current API contract, YDB storage, Terraform deployment, and verification.
- [docs/plans/contact-submissions.md](docs/plans/contact-submissions.md): agreed scope and acceptance criteria; describes the original implementation plan, not current runtime state.

## Working rules

- Keep the site simple, responsive, and in Russian. Do not add pages or make decorative buttons functional unless requested.
- Preserve `src/ContactFormDialog.jsx`, its submission flow, and the “Отправить” click goal `contact_form_submit_click` for Metrica counter `113655208`, unless the task explicitly changes them. Never send message text or contact details to analytics.
- Follow the current API documentation for contact work. Email notifications are a future iteration.
- Keep unrelated changes intact. Never commit credentials, Terraform state, or plans.
- Use Context7 MCP for current library, framework, SDK, API, CLI, or cloud documentation: resolve the library ID first, then query the relevant concept. This is unnecessary for documentation-only edits or general programming concepts.
- Run `npm run build` after frontend changes. For contact/backend/infrastructure changes, also run the relevant checks listed in [docs/contact-api.md](docs/contact-api.md).
