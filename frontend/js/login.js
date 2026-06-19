import { login, redirectIfAuthenticated } from './auth.js';
import { $ } from './utils.js';

if (redirectIfAuthenticated()) {
  // already redirecting
} else {
  const form = $('#login-form');
  const errorEl = $('#login-error');
  const submitBtn = $('#login-btn');

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    errorEl.hidden = true;

    const loginName = $('#login').value.trim();
    const password = $('#password').value;

    if (!loginName || !password) {
      errorEl.textContent = 'Введите логин и пароль';
      errorEl.hidden = false;
      return;
    }

    submitBtn.disabled = true;
    submitBtn.textContent = 'Вход…';

    try {
      await login(loginName, password);
      window.location.replace('matrix.html');
    } catch (err) {
      errorEl.textContent = err.message || 'Не удалось войти';
      errorEl.hidden = false;
      submitBtn.disabled = false;
      submitBtn.textContent = 'Войти';
    }
  });
}
