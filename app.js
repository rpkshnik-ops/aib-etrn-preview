const form = document.querySelector('[data-lead-form]');
const contactTypeInputs = [...document.querySelectorAll('input[name="contact_type"]')];
const symptomButtons = [...document.querySelectorAll('[data-symptom]')];
const selectionStatus = document.querySelector('.selection-status');
const formStatus = document.querySelector('[data-form-status]');
const submitButton = form?.querySelector('.form-submit');
const submitButtonContent = submitButton?.innerHTML;
const formEndpoint = document.body.dataset.formEndpoint || '';
const retrySeconds = Number(document.body.dataset.formRetrySeconds || 30);
const duplicateMinutes = Number(document.body.dataset.formDuplicateMinutes || 10);
const analyticsCounter = document.body.dataset.analyticsCounter || '';
let formStarted = false;
let isSubmitting = false;

const allowedEvents = new Set([
  'cta_click',
  'form_start',
  'form_error',
  'lead_accepted',
  'contact_click',
]);

function safeAnalyticsPayload(name, payload) {
  if (name === 'cta_click') {
    return { placement: String(payload.placement || 'unknown').slice(0, 40) };
  }
  if (name === 'form_error') {
    return { fields: String(payload.fields || '').slice(0, 100) };
  }
  if (name === 'contact_click') {
    return { channel: payload.channel === 'email' ? 'email' : 'phone' };
  }
  return {};
}

function installMetrica() {
  if (!/^\d{5,12}$/.test(analyticsCounter)) return;
  window.ym = window.ym || function () {
    (window.ym.a = window.ym.a || []).push(arguments);
  };
  window.ym.l = Date.now();
  if (!document.querySelector('script[data-aib-metrica]')) {
    const script = document.createElement('script');
    script.async = true;
    script.src = 'https://mc.yandex.ru/metrika/tag.js';
    script.dataset.aibMetrica = 'true';
    document.head.append(script);
  }
  window.ym(Number(analyticsCounter), 'init', {
    clickmap: false,
    trackLinks: false,
    accurateTrackBounce: true,
    webvisor: false,
  });
}

function track(name, payload = {}) {
  if (!allowedEvents.has(name)) return;
  const safePayload = safeAnalyticsPayload(name, payload);
  window.dispatchEvent(
    new CustomEvent('aib:analytics', {
      detail: { name, ...safePayload },
    })
  );
  if (/^\d{5,12}$/.test(analyticsCounter) && typeof window.ym === 'function') {
    window.ym(Number(analyticsCounter), 'reachGoal', name, safePayload);
  }
}

function safeUtm() {
  const params = new URLSearchParams(window.location.search);
  const allowed = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term'];
  return Object.fromEntries(
    allowed
      .map((key) => [key, params.get(key)])
      .filter(([, value]) => value && /^[\p{L}\p{N}._ -]{1,100}$/u.test(value))
  );
}

window.aibSite = {
  track,
  utm: safeUtm(),
  analyticsEnabled: /^\d{5,12}$/.test(analyticsCounter),
};

document.querySelectorAll('[data-cta]').forEach((link) => {
  link.addEventListener('click', () => {
    track('cta_click', { placement: link.dataset.placement || 'unknown' });
  });
});

document.querySelectorAll('[data-contact]').forEach((link) => {
  link.addEventListener('click', () => {
    track('contact_click', { channel: link.dataset.channel });
  });
});

function showContactField(type) {
  document.querySelectorAll('[data-contact-field]').forEach((field) => {
    const isActive = field.dataset.contactField === type;
    field.hidden = !isActive;
    const input = field.querySelector('input');
    input.disabled = !isActive;
    input.toggleAttribute('required', isActive);
    if (!isActive) clearFieldError(input);
  });
}

contactTypeInputs.forEach((input) => {
  input.addEventListener('change', () => showContactField(input.value));
});

function markFormStarted() {
  if (formStarted) return;
  formStarted = true;
  track('form_start', { placement: 'lead_form' });
}

form?.addEventListener('input', markFormStarted);
form?.addEventListener('change', markFormStarted);

function setFieldError(input, message) {
  const error = document.querySelector(`#${input.id}-error`);
  input.setAttribute('aria-invalid', 'true');
  if (error) error.textContent = message;
}

function clearFieldError(input) {
  if (!input) return;
  const error = document.querySelector(`#${input.id}-error`);
  input.removeAttribute('aria-invalid');
  if (error) error.textContent = '';
}

function validateForm() {
  const errors = [];
  const contactType = form.elements.contact_type.value;
  const contactInput = form.elements[contactType];
  const problem = form.elements.problem;
  const consent = form.elements.consent;

  [form.elements.phone, form.elements.email, problem, consent].forEach(clearFieldError);

  if (contactType === 'phone') {
    const digits = contactInput.value.replace(/\D/g, '');
    if (digits.length < 10 || digits.length > 15) {
      setFieldError(contactInput, 'Укажите телефон: от 10 до 15 цифр.');
      errors.push('phone');
    }
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(contactInput.value.trim())) {
    setFieldError(contactInput, 'Укажите корректный email.');
    errors.push('email');
  }

  if (problem.value.trim().length < 20) {
    setFieldError(problem, 'Опишите проблему хотя бы в 20 символах.');
    errors.push('problem');
  }

  if (!consent.checked) {
    setFieldError(consent, 'Нужно подтвердить согласие на обработку данных.');
    errors.push('consent');
  }

  return errors;
}

function showFormStatus(kind, message) {
  formStatus.className = `form-status form-status--${kind}`;
  formStatus.textContent = message;
}

function storageRead(key) {
  try {
    return window.sessionStorage.getItem(key);
  } catch {
    return null;
  }
}

function storageWrite(key, value) {
  try {
    window.sessionStorage.setItem(key, value);
  } catch {
    // Отправка продолжает работать, даже если sessionStorage недоступен.
  }
}

function formFingerprint() {
  const contactType = form.elements.contact_type.value;
  const contact = form.elements[contactType].value.trim().toLowerCase();
  const problem = form.elements.problem.value.trim().replace(/\s+/g, ' ').toLowerCase();
  const source = `${contactType}|${contact}|${problem}`;
  let hash = 2166136261;
  for (let index = 0; index < source.length; index += 1) {
    hash ^= source.charCodeAt(index);
    hash = Math.imul(hash, 16777619);
  }
  return (hash >>> 0).toString(16);
}

function requestId() {
  if (typeof crypto?.randomUUID === 'function') return crypto.randomUUID();
  return `aib-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function buildPayload(id) {
  const payload = new FormData(form);
  payload.delete('consent');
  payload.set('_subject', 'Тестовая заявка с лендинга «Компания АиБ»');
  payload.set('_template', 'table');
  payload.set('request_id', id);
  payload.set('page_url', `${window.location.origin}${window.location.pathname}`);
  payload.set('submitted_at', new Date().toISOString());
  Object.entries(safeUtm()).forEach(([key, value]) => payload.set(key, value));
  return payload;
}

async function parseResponse(response) {
  const raw = await response.text();
  let data = {};
  try {
    data = raw ? JSON.parse(raw) : {};
  } catch {
    data = { message: raw };
  }
  const accepted = data.success === true || data.success === 'true';
  if (!response.ok || !accepted) {
    const error = new Error(data.message || `Сервер вернул код ${response.status}.`);
    error.status = response.status;
    throw error;
  }
  return data;
}

form?.addEventListener('submit', async (event) => {
  event.preventDefault();
  if (isSubmitting) return;

  const errors = validateForm();
  if (errors.length) {
    track('form_error', { fields: errors.join(',') });
    showFormStatus('error', 'Проверьте отмеченные поля. Введённые данные сохранены.');
    form.querySelector('[aria-invalid="true"]')?.focus();
    return;
  }

  if (!formEndpoint) {
    track('form_error', { fields: 'endpoint' });
    showFormStatus('error', 'Канал отправки не настроен. Позвоните или напишите нам по контактам внизу страницы.');
    return;
  }

  const now = Date.now();
  const fingerprint = formFingerprint();
  let lastAccepted = null;
  try {
    lastAccepted = JSON.parse(storageRead('aib:last-accepted') || 'null');
  } catch {
    lastAccepted = null;
  }
  const duplicateWindow = duplicateMinutes * 60 * 1000;
  if (
    lastAccepted &&
    lastAccepted.fingerprint === fingerprint &&
    now - Number(lastAccepted.at) < duplicateWindow
  ) {
    showFormStatus('success', 'Эта заявка уже принята. Повторно отправлять её не нужно.');
    return;
  }

  const lastAttempt = Number(storageRead('aib:last-attempt') || 0);
  const secondsLeft = Math.ceil((retrySeconds * 1000 - (now - lastAttempt)) / 1000);
  if (lastAttempt && secondsLeft > 0) {
    showFormStatus('error', `Повторить отправку можно через ${secondsLeft} сек. Данные сохранены.`);
    return;
  }

  if (form.elements._honey.value) {
    showFormStatus('error', 'Не удалось отправить форму. Обновите страницу и попробуйте ещё раз.');
    return;
  }

  isSubmitting = true;
  storageWrite('aib:last-attempt', String(now));
  submitButton.disabled = true;
  submitButton.setAttribute('aria-disabled', 'true');
  submitButton.textContent = 'Отправляем…';
  showFormStatus('sending', 'Передаём заявку защищённому обработчику…');

  try {
    const response = await fetch(formEndpoint, {
      method: 'POST',
      headers: { Accept: 'application/json' },
      body: buildPayload(requestId()),
    });
    await parseResponse(response);
    storageWrite(
      'aib:last-accepted',
      JSON.stringify({ fingerprint, at: Date.now() })
    );
    track('lead_accepted');
    showFormStatus('success', 'Заявка принята. Ответим в течение 2 рабочих часов.');
    form.reset();
    showContactField('phone');
    formStarted = false;
  } catch (error) {
    track('form_error', { fields: error.status === 429 ? 'rate_limit' : 'server' });
    const message = error.status === 429
      ? 'Слишком много попыток. Подождите несколько минут и отправьте заявку снова.'
      : 'Не удалось подтвердить приём заявки. Данные сохранены — проверьте соединение и повторите отправку.';
    showFormStatus('error', message);
  } finally {
    submitButton.disabled = false;
    submitButton.removeAttribute('aria-disabled');
    submitButton.innerHTML = submitButtonContent;
    isSubmitting = false;
  }
});

symptomButtons.forEach((button) => {
  button.addEventListener('click', () => {
    const wasSelected = button.getAttribute('aria-pressed') === 'true';
    symptomButtons.forEach((item) => item.setAttribute('aria-pressed', 'false'));
    button.setAttribute('aria-pressed', String(!wasSelected));

    if (wasSelected) {
      selectionStatus.textContent = 'Симптом не выбран. Можно описать ситуацию своими словами.';
      return;
    }

    const problem = form.elements.problem;
    const prefix = `Симптом: ${button.dataset.symptom}. `;
    if (!problem.value.trim() || problem.value.startsWith('Симптом:')) {
      problem.value = prefix;
    }
    selectionStatus.textContent = `«${button.dataset.symptom}» добавлено в черновик заявки.`;
  });
});

document.querySelectorAll('[data-open-dialog]').forEach((button) => {
  button.addEventListener('click', () => {
    const dialog = document.querySelector(`#${button.dataset.openDialog}`);
    if (typeof dialog?.showModal === 'function') dialog.showModal();
  });
});

document.querySelectorAll('.faq-item').forEach((item) => {
  item.addEventListener('toggle', () => {
    const icon = item.querySelector('summary span');
    if (icon) icon.textContent = item.open ? '−' : '+';
  });
});

installMetrica();
showContactField('phone');
