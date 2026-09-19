const body = document.body;
const variantButtons = [...document.querySelectorAll('[data-set-variant]')];
const dialog = document.querySelector('#prototype-dialog');
const symptomButtons = [...document.querySelectorAll('[data-symptom]')];
const selectionStatus = document.querySelector('.selection-status');

function setVariant(variant, updateUrl = true) {
  const nextVariant = variant === 'b' ? 'b' : 'a';
  body.dataset.variant = nextVariant;
  variantButtons.forEach((button) => {
    button.setAttribute('aria-pressed', String(button.dataset.setVariant === nextVariant));
  });

  if (updateUrl) {
    const url = new URL(window.location.href);
    url.searchParams.set('variant', nextVariant);
    window.history.replaceState({}, '', url);
  }
}

variantButtons.forEach((button) => {
  button.addEventListener('click', () => setVariant(button.dataset.setVariant));
});

document.querySelectorAll('[data-prototype-cta]').forEach((link) => {
  link.addEventListener('click', (event) => {
    if (typeof dialog.showModal !== 'function') return;
    event.preventDefault();
    dialog.showModal();
  });
});

symptomButtons.forEach((button) => {
  button.addEventListener('click', () => {
    const isSelected = button.getAttribute('aria-pressed') === 'true';
    symptomButtons.forEach((item) => item.setAttribute('aria-pressed', 'false'));
    button.setAttribute('aria-pressed', String(!isSelected));
    selectionStatus.textContent = isSelected
      ? 'Симптом не выбран. Важный контент остаётся доступен без выбора.'
      : `Выбрано: «${button.dataset.symptom}». На следующем этапе этот текст попадёт в черновик заявки.`;
  });
});

const initialVariant = new URLSearchParams(window.location.search).get('variant');
setVariant(initialVariant, false);
