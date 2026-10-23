export function normalizeContact(message, contacts) {
  const values = { message: message.trim(), contacts: contacts.trim() };
  if (!values.message || !values.contacts) throw new Error('Заполните оба поля.');
  if ([...values.message].length > 1000 || [...values.contacts].length > 100) {
    throw new Error('Сообщение — до 1000 символов, контакты — до 100 символов.');
  }
  return values;
}

export async function sendContact(url, payload, fetcher = fetch, timeout = 15000) {
  if (!url) throw new Error('Форма временно недоступна. Попробуйте позже.');
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeout);
  try {
    const response = await fetcher(url, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload), signal: controller.signal,
    });
    if (response.status === 429) throw new Error('Слишком много заявок. Повторите через 10 минут.');
    if (response.status === 409) throw new Error('Эта попытка уже принята с другим содержимым. Откройте форму заново.');
    if (!response.ok) throw new Error('Не удалось сохранить заявку. Повторите отправку.');
    const result = await response.json();
    if (result.status !== 'saved' || result.id !== payload.id) throw new Error('Сохранение не подтверждено. Повторите отправку.');
  } catch (error) {
    if (error.name === 'AbortError' || error instanceof TypeError) {
      throw new Error('Нет ответа сервера. Проверьте соединение и повторите отправку.');
    }
    throw error;
  } finally {
    clearTimeout(timer);
  }
}
