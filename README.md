# Hexlet AI Automator — React SPA

A Russian-language, single-page fitness club concept with Lucide icons and fitness photo slots. All promotional buttons are decorative; “Написать нам” opens the original contact dialog.

## Run locally

```sh
npm install
npm run dev
```

To create a production build, run `npm run build`.

## Background video

The fullscreen hero currently uses an Unsplash photo as its background. Photo URLs live in the `photos` object in `src/main.jsx`; replace them with your own local assets when ready. External photos need network access; a gradient background remains if they are unavailable. To add your video, place it at `public/club-background.mp4` and add `VITE_HERO_VIDEO=club-background.mp4` to `.env.local`, then restart the dev server or rebuild. The video plays muted, loops, and fills the hero. The photo remains as its poster and reduced-motion fallback.

## Yandex Metrica

Counter `113655208` tracks clicks on the contact form's “Отправить” button with
the JavaScript event goal `contact_form_submit_click`. In this counter's settings,
create a goal of type “JavaScript event” with that exact identifier.

The goal records each button click, including clicks with empty fields. It does
not confirm delivery: delivery is confirmed separately by the API after saving to YDB.
The goal call does not include message text or contact details.

## Publish on GitHub Pages

1. Push this project to a GitHub repository on the `main` branch.
2. In the repository, open **Settings → Pages** and set **Build and deployment → Source** to **GitHub Actions**.
3. Open the **Actions** tab and wait for the **Deploy to GitHub Pages** workflow to finish.
4. Open the published URL shown in the workflow run or under **Settings → Pages**.

The workflow builds the app and deploys the `dist` directory. The Vite base path is set automatically from the repository name in GitHub Actions. If your default branch is not `main`, update the branch under `on.push.branches` in `.github/workflows/deploy.yml`.

## Contact submissions

Set `VITE_CONTACT_API_URL` in `.env.local` for development and in the GitHub repository Actions variables for Pages builds. Without it the form reports that it is unavailable. See [deployment and verification](docs/contact-api.md) for Terraform, the API contract, and acceptance checks.

## Fitness dashboard

Open `/#/dashboard` locally or append `#/dashboard` to the GitHub Pages project URL. The default demonstration mode needs no cloud credentials. For connected sources, setup and deployment steps are in [the webinar guide](docs/dashboard-webinar.md).

## Deploy infrastructure to Yandex Cloud

Copy `infra/deploy.example.json` to `infra/deploy.local.json` and set your cloud ID, folder ID, and path to the authorized service-account JSON key. The local configuration and key are excluded from Git.

```sh
npm run deploy -- --plan  # preview changes
npm run deploy           # initialize, validate, show plan and apply after confirmation
```

For unattended deployment use `npm run deploy -- --auto-approve`. The command prints the API URL after applying; set it as `VITE_CONTACT_API_URL` for the separate Pages build. Environment variables `YC_CLOUD_ID`, `YC_FOLDER_ID`, and `YC_SERVICE_ACCOUNT_KEY_FILE` override local configuration (`TF_VAR_cloud_id`/`TF_VAR_folder_id` take precedence over the YC IDs). Terraform must be installed and the service account must have deployment permissions. See [deployment details](docs/contact-api.md).

## Telegram test function

`npm run deploy` also deploys a public Python function and prints `telegram_function_url`.
Set `BOT_TOKEN` and `ADMIN_CHAT_ID` in the deployment environment, or add string fields
`bot_token` and `admin_chat_id` to ignored `infra/deploy.local.json`.
`TF_VAR_bot_token` and `TF_VAR_admin_chat_id` take precedence.
The token is marked sensitive in Terraform, but is still stored in local Terraform state;
keep state private.

Open the printed URL to send a default greeting, or append `?text=Hello` to send custom text.
The recipient must first start the bot. Every GET sends a new message; anyone with the
public URL can trigger it. The function is a standalone test endpoint, not a Telegram webhook
or an automatic notification from the contact form. It has no database permissions.
Source: `backend/telegram_function.py`; infrastructure: `infra/telegram.tf`.

### Telegram function version

After `npm run deploy`, open the printed Telegram URL with `?version` (or
`?version=1`). It returns `{"service":"telegram-function","version":"1.0.2"}`
without requiring bot credentials or sending a message. Responses disable caching.
The handler version is defined by `FUNCTION_VERSION` in `backend/telegram_function.py`
and is independent of the frontend and AWS proxy versions.

Telegram handler 1.0.2 sends requests through the AWS reverse proxy at
`https://jkvsndafl2.execute-api.us-east-1.amazonaws.com` with `destination=telegram`.
It no longer contacts Telegram directly. Network diagnostics report the AWS host
and identify Telegram separately as the upstream. Redeploy with `npm run deploy`;
the Terraform archive hash automatically picks up the handler change.
