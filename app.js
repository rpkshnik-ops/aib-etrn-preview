const form = document.querySelector('[data-lead-form]');
const contactTypeInputs = [...document.querySelectorAll('input[name="contact_type"]')];
const symptomButtons = [...document.querySelectorAll('[data-symptom]')];
const selectionStatus = document.querySelector('.selection-status');
const formStatus = document.querySelector('[data-form-status]');
const submitButton = form?.querySelector('.form-submit');
let formStarted = false;
let isSubmitting = false;

const allowedEvents = new Set([
  'cta_click',
  'form_start',
  'form_error',
  'lead_accepted',
  'contact_click',
]);

function track(name, payload = {}) {
  if (!allowedEvents.has(name)) return;
  window.dispatchEvent(
    new CustomEvent('aib:analytics', {
      detail: { name, ...payload },
    })
  );
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

window.aibPreview = { track, utm: safeUtm() };

document.querySelectorAll('[data-cta]').forEach((link) => {
  link.addEventListener('click', () => {
    track('cta_click', { placement: link.dataset.placement || 'unknown' });
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

form?.addEventListener('input', markFormStarted, { once: true });
form?.addEventListener('change', markFormStarted, { once: true });

function setFieldError(input, message) {
  const error = document.querySelector(`#${input.id}-error`);
  input.setAttribute('aria-invalid', 'true');
  if (error) error.textContent = message;
}

function clearFieldError(input) {
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

form?.addEventListener('submit', (event) => {
  event.preventDefault();
  if (isSubmitting) return;

  const errors = validateForm();
  if (errors.length) {
    track('form_error', { fields: errors.join(',') });
    showFormStatus('error', 'Проверьте отмеченные поля. Введённые данные сохранены.');
    form.querySelector('[aria-invalid="true"]')?.focus();
    return;
  }

  isSubmitting = true;
  submitButton.disabled = true;
  submitButton.setAttribute('aria-disabled', 'true');
  showFormStatus(
    'preview',
    'Отправка пока не подключена. Данные остались в форме и никуда не переданы. После подтверждения канала здесь появится реальная доставка заявки.'
  );
  submitButton.disabled = false;
  submitButton.removeAttribute('aria-disabled');
  isSubmitting = false;
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

showContactField('phone');
