# Hexlet AI Automator — React SPA

A minimal React single-page application that displays a “Hello, world!” page.

## Run locally

```sh
npm install
npm run dev
```

To create a production build, run `npm run build`.

## Yandex Metrica

Counter `113655208` tracks clicks on the contact form's “Отправить” button with
the JavaScript event goal `contact_form_submit_click`. In this counter's settings,
create a goal of type “JavaScript event” with that exact identifier.

The goal records each button click, including clicks with empty fields. It does
not confirm delivery: the form currently only displays a local success message.
The goal call does not include message text or contact details.

## Publish on GitHub Pages

1. Push this project to a GitHub repository on the `main` branch.
2. In the repository, open **Settings → Pages** and set **Build and deployment → Source** to **GitHub Actions**.
3. Open the **Actions** tab and wait for the **Deploy to GitHub Pages** workflow to finish.
4. Open the published URL shown in the workflow run or under **Settings → Pages**.

The workflow builds the app and deploys the `dist` directory. The Vite base path is set automatically from the repository name in GitHub Actions. If your default branch is not `main`, update the branch under `on.push.branches` in `.github/workflows/deploy.yml`.
