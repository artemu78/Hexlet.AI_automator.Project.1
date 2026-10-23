import { access, readFile } from 'node:fs/promises';
import { constants } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { resolve, isAbsolute } from 'node:path';

const root = fileURLToPath(new URL('../', import.meta.url));
const configPath = resolve(root, 'infra/deploy.local.json');

async function main() {
  const args = process.argv.slice(2);
  if (args.some((arg) => !['--plan', '--auto-approve'].includes(arg))) {
    throw new Error('Используйте npm run deploy [-- --plan | -- --auto-approve].');
  }
  let config = {};
  try {
    config = JSON.parse(await readFile(configPath, 'utf8'));
  } catch (error) {
    if (error.code !== 'ENOENT') throw new Error('Не удалось прочитать infra/deploy.local.json. Проверьте JSON.');
  }
  const cloud = process.env.TF_VAR_cloud_id || process.env.YC_CLOUD_ID || config.cloud_id;
  const folder = process.env.TF_VAR_folder_id || process.env.YC_FOLDER_ID || config.folder_id;
  const key = process.env.YC_SERVICE_ACCOUNT_KEY_FILE || config.service_account_key_file;
  if (!cloud || !folder || !key) {
    throw new Error('Укажите cloud_id, folder_id и service_account_key_file в infra/deploy.local.json (образец: infra/deploy.example.json) или задайте YC_CLOUD_ID, YC_FOLDER_ID, YC_SERVICE_ACCOUNT_KEY_FILE.');
  }
  const keyPath = isAbsolute(key) ? key : resolve(root, key);
  try {
    await access(keyPath, constants.R_OK);
    const credential = JSON.parse(await readFile(keyPath, 'utf8'));
    if (!credential.service_account_id || !credential.private_key || !credential.id) throw new Error();
  } catch {
    throw new Error('Файл авторизованного ключа недоступен или не содержит корректный ключ сервисного аккаунта.');
  }
  const env = {
    ...process.env,
    YC_SERVICE_ACCOUNT_KEY_FILE: keyPath,
    TF_VAR_cloud_id: cloud,
    TF_VAR_folder_id: folder,
  };
  // The provider accepts only one authentication method. Use the requested key.
  delete env.YC_TOKEN;
  function terraform(...command) {
    const result = spawnSync('terraform', ['-chdir=infra', ...command], {
      cwd: root, env, stdio: 'inherit', shell: false,
    });
    if (result.error?.code === 'ENOENT') throw new Error('Terraform не найден в PATH. Установите Terraform >= 1.5.');
    if (result.error || result.signal || result.status !== 0) {
      throw new Error(`Terraform ${command[0]} завершился с ошибкой. Развёртывание остановлено.`);
    }
  }
  terraform('init', '-input=false');
  terraform('fmt', '-check');
  terraform('validate');
  if (args.includes('--plan')) {
    terraform('plan', '-input=false');
  } else {
    terraform('apply', ...(args.includes('--auto-approve') ? ['-auto-approve', '-input=false'] : []));
    console.log('\nПубличный URL для VITE_CONTACT_API_URL:');
    terraform('output', '-raw', 'contact_api_url');
    console.log();
  }
}

main().catch((error) => {
  console.error(error.message);
  process.exitCode = 1;
});
