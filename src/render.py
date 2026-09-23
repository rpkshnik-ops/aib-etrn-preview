from html import escape

from .site_config import SITE_CONFIG as config
from .deployment import settings


CTA_ICON = """<span class="button__icon" aria-hidden="true"><svg viewBox="0 0 20 20" focusable="false"><path d="M5 15 15 5M8 5h7v7"/></svg></span>"""


def e(value):
    return escape(str(value), quote=True)


def render_symptoms():
    cards = []
    for index, symptom in enumerate(config["symptoms"], start=1):
        cards.append(
            f"""
        <button class="symptom-card" type="button" data-symptom="{e(symptom['title'])}" data-cta data-placement="symptom_card" aria-pressed="false">
          <span class="symptom-card__number" aria-hidden="true">{index:02d}</span>
          <span class="symptom-card__title">{e(symptom['title'])}</span>
          <span class="symptom-card__text">{e(symptom['text'])}</span>
          <span class="symptom-card__action"><span class="symptom-card__action-label">Добавить в заявку</span> {CTA_ICON}</span>
        </button>"""
        )
    return "".join(cards)


def render_faq():
    items = (
        (
            "С какими системами вы работаете?",
            "Рассматриваем задачи в 1С, TMS, модулях и сервисах ЭДО, а также при обмене ЭТрН и формировании ЭПЛ. Конкретные системы и версии фиксируем в заявке после первичного анализа.",
        ),
        (
            "Что делать, если ошибок несколько?",
            "Определим, относятся ли симптомы к одной причине. Несколько независимых проблем оформляются отдельными согласованными заявками.",
        ),
        (
            "Если сбой на стороне оператора ЭДО?",
            "Поможем локализовать причину и подготовить дальнейшие действия. Мы не можем устранить инфраструктурный сбой оператора, если он не связан с нашими работами.",
        ),
        (
            "Нужен ли удалённый доступ?",
            "Все работы выполняем удалённо. При необходимости диагностики заранее согласуем доступ и безопасный способ подключения — пароли и ключи электронной подписи через публичную форму не запрашиваем.",
        ),
        (
            "Сколько занимает работа?",
            "Ориентир — 1–5 рабочих дней после предоплаты и получения необходимых доступов и информации. Точный срок фиксируем в заявке.",
        ),
        (
            "Что входит в 130 000 ₽?",
            "Первичный анализ, диагностика причины, согласованный объём исправлений, проверка результата и закрывающие документы в рамках одной заявки.",
        ),
        (
            "Как действует гарантия?",
            "На выполненные работы предусмотрена гарантия 14 дней. Границы гарантийного случая и порядок обращения фиксируем в заявке.",
        ),
        (
            "Что происходит, если проблему решить нельзя?",
            "До оплаты согласуем ожидаемый результат и условия возврата для причин в нашей зоне ответственности. Безусловный возврат при внешних ограничениях оператора, контрагента или программного обеспечения не обещаем.",
        ),
    )
    return "".join(
        f"""
        <details class="faq-item">
          <summary>{e(question)}<span aria-hidden="true">+</span></summary>
          <div class="faq-item__content">
            <div class="faq-item__content-inner"><p>{e(answer)}</p></div>
          </div>
        </details>"""
        for question, answer in items
    )


def render_page(options=None, asset_version="dev"):
    options = settings(options)
    preview = options['mode'] == 'preview'
    production = options['mode'] == 'production'
    company = config["company"]
    service = config["service"]
    contacts = config["contacts"]
    form_config = config["form"]
    analytics = config["analytics"]
    analytics_counter = options['metrica_id'] if production else ''
    rubles = f"{service['price']:,}".replace(",", " ")
    endpoint = form_config['endpoint'] if preview else '/api/leads'
    canonical = f'<link rel="canonical" href="{e(options["site_url"])}"><meta property="og:url" content="{e(options["site_url"])}">' if production else ''
    def document_link(key, label, fallback):
        if options[key]:
            return f'<a class="inline-link" href="{e(options[key])}" target="_blank" rel="noopener">{label}</a>'
        return f'<button type="button" class="inline-link" data-open-dialog="{fallback}">{label}</button>'
    privacy_link = document_link('privacy_url', 'Обработка данных', 'privacy-dialog')
    consent_link = document_link('consent_url', 'Текст согласия', 'privacy-dialog')
    offer_url = options['offer_url'] or 'assets/documents/offer.pdf?v=20260923'
    offer_link = f'<a href="{e(offer_url)}" target="_blank" rel="noopener">Публичная оферта · PDF</a>'

    return f"""<!doctype html>
<html lang="ru">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="robots" content="{'index, follow' if production else 'noindex, nofollow'}">
    {canonical}
    <meta name="theme-color" content="#171914">
    <title>Решение проблем с ЭТрН — {rubles} ₽ | {e(company['public_name'])}</title>
    <meta name="description" content="Удалённая диагностика и устранение согласованных проблем с ЭТрН, ЭПЛ, ЭДО, 1С и TMS. Одна согласованная заявка — {rubles} ₽, НДС 5%.">
    <meta property="og:type" content="website">
    <meta property="og:locale" content="ru_RU">
    <meta property="og:title" content="Поможем решить проблему с ЭТрН">
    <meta property="og:description" content="Диагностика и согласованный объём исправлений — {rubles} ₽ за заявку.">
    <link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='16' fill='%23f4c400'/%3E%3Cpath d='M15 37h12l7-14h15' fill='none' stroke='%23171914' stroke-width='6' stroke-linecap='round' stroke-linejoin='round'/%3E%3Ccircle cx='15' cy='37' r='5' fill='%23171914'/%3E%3Ccircle cx='49' cy='23' r='5' fill='%23171914'/%3E%3C/svg%3E">
    <link rel="stylesheet" href="styles.css?v={e(asset_version)}">
    <script src="app.js?v={e(asset_version)}" defer></script>
  </head>
  <body
    data-variant="b"
    data-preview="{str(not production).lower()}"
    data-form-mode="{'testing' if preview else 'live'}"
    data-form-endpoint="{e(endpoint)}"
    data-form-retry-seconds="{e(form_config['minimum_retry_seconds'])}"
    data-form-duplicate-minutes="{e(form_config['duplicate_window_minutes'])}"
    data-analytics-provider="{e(analytics['provider'])}"
    data-analytics-counter="{e(analytics_counter)}"
  >
    <a class="skip-link" href="#main">К содержанию</a>

    <header class="site-header site-header--final">
      <div class="site-header__inner">
        <a class="brand" href="#top" aria-label="{e(company['public_name'])} — в начало страницы">
          <span class="brand__mark" aria-hidden="true">
            <img src="assets/aib-logo.png" alt="" width="100" height="66">
          </span>
          <span class="brand__text">{e(company['public_name'])}</span>
        </a>
        <nav class="site-nav" aria-label="Основная навигация">
          <a href="#problems">Проблемы</a>
          <a href="#scope">Что входит</a>
          <a href="#process">Порядок работы</a>
          <a href="#price">Стоимость</a>
        </nav>
        <a class="header-cta" href="#request" data-cta data-placement="header">Обсудить проблему</a>
      </div>
    </header>

    <a class="floating-cta" href="#request" data-floating-cta data-cta data-placement="mobile_floating" aria-hidden="true" tabindex="-1">
      Обсудить проблему {CTA_ICON}
    </a>

    <main id="main">
      <section class="hero hero--final" id="top" aria-labelledby="hero-title">
        <div class="hero__glow hero__glow--one" aria-hidden="true"></div>
        <div class="hero__glow hero__glow--two" aria-hidden="true"></div>
        <div class="hero__grid">
          <div class="hero__copy">
            <p class="eyebrow"><span aria-hidden="true"></span> Техническая помощь для бизнеса</p>
            <h1 id="hero-title">{e(service['headline'])}</h1>
            <p class="hero__lead">Диагностируем причину и устраняем согласованные ошибки ЭТрН, ЭПЛ и электронного документооборота — от подписи до обмена между 1С, TMS и оператором ЭДО.</p>
            <div class="hero__actions">
              <a class="button button--primary" href="#request" data-cta data-placement="hero">Обсудить проблему {CTA_ICON}</a>
              <a class="button button--text" href="#scope">Что входит в стоимость <span aria-hidden="true">↓</span></a>
            </div>
          </div>

          <ul class="hero__facts" aria-label="Ключевые условия">
            <li><span aria-hidden="true">01</span> Ответим в течение 2 рабочих часов</li>
            <li><span aria-hidden="true">02</span> Объём и срок закрепим в заявке</li>
            <li><span aria-hidden="true">03</span> Акт и гарантия 14 дней</li>
          </ul>

          <aside class="price-panel" id="hero-price" aria-label="Стоимость и условия">
            <p class="price-panel__label">Стоимость</p>
            <p class="price-panel__value">{rubles}<span> ₽</span></p>
            <p class="price-panel__unit">{e(service['price_unit'])}</p>
            <div class="price-panel__rule"></div>
            <p class="price-panel__prepay">{e(service['prepayment'])} · {e(service['tax'])}</p>
            <p class="price-panel__note">{e(service['scope_note'])}</p>
          </aside>

          <figure class="flow-visual" aria-label="Схема маршрута электронного документа">
            <div class="flow-visual__signal flow-visual__signal--one" aria-hidden="true"></div>
            <div class="flow-visual__signal flow-visual__signal--two" aria-hidden="true"></div>
            <div class="flow-visual__route" aria-hidden="true"></div>
            <svg class="flow-visual__pulse" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true" focusable="false">
              <ellipse cx="50" cy="50" rx="49" ry="49" pathLength="100" />
            </svg>
            <div class="flow-node flow-node--start"><span>01</span> Создание</div>
            <div class="flow-node flow-node--sign"><span>02</span> Подписание</div>
            <div class="flow-node flow-node--send"><span>03</span> Передача</div>
            <div class="document-card">
              <div class="document-card__top">
                <span class="document-card__icon" aria-hidden="true">
                  <svg viewBox="0 0 24 24" focusable="false"><path d="M7 2.75h7.2L19.25 7.8V21.25H7z"/><path d="M14 2.75V8h5.25M10 12h6M10 15.5h6M10 19h4"/></svg>
                </span>
                <span>Электронный перевозочный документ</span>
              </div>
              <div class="document-card__status"><span></span> Маршрут обмена</div>
              <div class="document-card__line document-card__line--wide"></div>
              <div class="document-card__line"></div>
              <div class="document-card__line document-card__line--short"></div>
              <div class="document-card__check" aria-hidden="true">✓</div>
            </div>
          </figure>
        </div>
      </section>

      <section class="promise-strip" aria-label="Условия работы">
        <div class="promise-strip__inner">
          <p><strong>2 часа</strong><span>на первый ответ в рабочее время</span></p>
          <p><strong>1–5 дней</strong><span>ориентир; точный срок в заявке</span></p>
          <p><strong>14 дней</strong><span>гарантия на выполненные работы</span></p>
          <p><strong>Удалённо</strong><span>все работы — без выезда в офис</span></p>
        </div>
      </section>

      <section class="symptoms" id="problems" aria-labelledby="symptoms-title">
        <div class="symptoms__heading">
          <p class="section-index">01 / Симптомы</p>
          <h2 id="symptoms-title">Узнаёте свою ситуацию?</h2>
          <p>Отметьте ближайший симптом — он появится в черновике заявки. Точную причину и границы работ определим после первичного уточнения.</p>
        </div>
        <div class="symptoms__grid">{render_symptoms()}</div>
        <p class="selection-status" aria-live="polite">Весь список доступен без выбора; кнопки только ускоряют заполнение формы.</p>
      </section>

      <section class="scope-section" id="scope" aria-labelledby="scope-title">
        <div class="content-shell">
          <div class="section-heading section-heading--split">
            <div>
              <p class="section-index">02 / Состав услуги</p>
              <h2 id="scope-title">Что входит в 130 000 ₽</h2>
            </div>
            <p>Одна услуга — одна согласованная проблема. До счёта фиксируем системы, ожидаемый результат, срок и границы ответственности.</p>
          </div>

          <div class="scope-grid">
            <article class="scope-card scope-card--wide">
              <span class="scope-card__index">01</span>
              <h3>Диагностика и поиск причины</h3>
              <p>Проверяем статусы, настройки, форматы, маршруты обмена и точки интеграции.</p>
            </article>
            <article class="scope-card">
              <span class="scope-card__index">02</span>
              <h3>ЭТрН и ЭДО</h3>
              <p>Ошибки отправки, получения, статусов, роуминга и взаимодействия участников.</p>
            </article>
            <article class="scope-card">
              <span class="scope-card__index">03</span>
              <h3>1С и TMS</h3>
              <p>Выгрузка, XML, форматы, кодировки, справочники и обмен с модулями ЭДО.</p>
            </article>
            <article class="scope-card">
              <span class="scope-card__index">04</span>
              <h3>Подпись, КЭП и МЧД</h3>
              <p>Сертификаты, полномочия, криптопровайдер и подписание документов.</p>
            </article>
            <article class="scope-card">
              <span class="scope-card__index">05</span>
              <h3>Электронные путевые листы</h3>
              <p>Титулы, обязательные поля, данные транспорта и формирование ЭПЛ.</p>
            </article>
            <article class="scope-card scope-card--accent">
              <span class="scope-card__index">06</span>
              <h3>Исправление и проверка</h3>
              <p>Выполняем согласованный объём изменений и проверяем результат на тестовом или рабочем документе.</p>
            </article>
          </div>

          <aside class="boundaries" aria-labelledby="boundaries-title">
            <div>
              <p class="section-index">Границы</p>
              <h3 id="boundaries-title">Что согласуем отдельно</h3>
            </div>
            <ul>
              <li>Покупку лицензий, сертификатов и услуг оператора ЭДО</li>
              <li>Индивидуальную разработку и новые программные модули</li>
              <li>Несколько независимых проблем и абонентское сопровождение</li>
            </ul>
          </aside>
        </div>
      </section>

      <section class="process-section" id="process" aria-labelledby="process-title">
        <div class="content-shell">
          <div class="section-heading section-heading--split section-heading--inverse">
            <div>
              <p class="section-index">03 / Порядок работы</p>
              <h2 id="process-title">От заявки до проверенного результата</h2>
            </div>
            <p>Не обещаем решение до установления причины. Сначала уточняем задачу, затем закрепляем объём и срок документально.</p>
          </div>
          <ol class="process-list">
            <li><span>01</span><div><h3>Заявка</h3><p>Контакт и краткое описание проблемы — без паролей, ключей и файлов.</p></div></li>
            <li><span>02</span><div><h3>Первичное уточнение</h3><p>Связываемся в течение 2 рабочих часов и собираем необходимый контекст.</p></div></li>
            <li><span>03</span><div><h3>Заявка и счёт</h3><p>Фиксируем системы, объём, ожидаемый результат, срок и условия возврата.</p></div></li>
            <li><span>04</span><div><h3>Предоплата</h3><p>100% безналичная оплата по выставленному счёту, НДС — 5%.</p></div></li>
            <li><span>05</span><div><h3>Диагностика и исправление</h3><p>Получаем согласованные доступы, находим причину и выполняем работы.</p></div></li>
            <li><span>06</span><div><h3>Проверка и акт</h3><p>Проверяем результат, передаём акт и условия 14-дневной гарантии.</p></div></li>
          </ol>
        </div>
      </section>

      <section class="pricing-section" id="price" aria-labelledby="price-title">
        <div class="content-shell pricing-layout">
          <div class="pricing-card">
            <p class="section-index">04 / Стоимость</p>
            <h2 id="price-title">{rubles}<span> ₽</span></h2>
            <p class="pricing-card__unit">за одну согласованную заявку</p>
            <p class="pricing-card__tax">100% предоплата · НДС — 5%</p>
            <a class="button button--dark" href="#request" data-cta data-placement="price">Обсудить проблему {CTA_ICON}</a>
          </div>
          <div class="pricing-copy">
            <h3>Сумма известна до начала работ</h3>
            <p>После первичного анализа в заявке фиксируем одну проблему, системы, ожидаемый результат и точный срок. Только затем выставляем счёт.</p>
            <dl class="terms-list">
              <div><dt>Если проблем несколько</dt><dd>Независимые причины оформляются отдельными заявками.</dd></div>
              <div><dt>Ориентир по сроку</dt><dd>1–5 рабочих дней после оплаты и предоставления необходимой информации.</dd></div>
              <div><dt>Если решение невозможно</dt><dd>Условия возврата для причин в нашей зоне ответственности закрепляем до оплаты.</dd></div>
            </dl>
          </div>
        </div>
      </section>

      <section class="trust-section" aria-labelledby="trust-title">
        <div class="content-shell trust-layout">
          <div>
            <p class="section-index">05 / Ответственность</p>
            <h2 id="trust-title">Работу закрепляем документами</h2>
          </div>
          <div class="trust-copy">
            <p class="trust-copy__lead">Исполнитель — {e(company['legal_name'])}. Объём и срок фиксируются в заявке, завершение подтверждается актом.</p>
            <div class="trust-points">
              <article><span>01</span><h3>Конфиденциальность</h3><p>Информацию и доступы используем только для согласованных работ.</p></article>
              <article><span>02</span><h3>Проверяемый результат</h3><p>Сценарий проверки определяем вместе до начала исправлений.</p></article>
              <article><span>03</span><h3>Закрывающие документы</h3><p>После выполнения направляем акт через согласованный канал.</p></article>
              <article><span>04</span><h3>Полностью удалённо</h3><p>Работаем без выезда в офис: подключение и проверку проводим согласованным безопасным способом.</p></article>
            </div>
            <p class="requisites">ИНН {e(company['inn'])} · КПП {e(company['kpp'])} · ОГРН {e(company['ogrn'])}</p>
          </div>
        </div>
      </section>

      <section class="faq-section" id="faq" aria-labelledby="faq-title">
        <div class="content-shell faq-layout">
          <div class="faq-heading">
            <p class="section-index">06 / Вопросы</p>
            <h2 id="faq-title">До отправки заявки</h2>
            <p>Не нашли свой сценарий? Опишите симптомы своими словами — без технических секретов и доступов.</p>
          </div>
          <div class="faq-list">{render_faq()}</div>
        </div>
      </section>

      <section class="lead-section" id="request" aria-labelledby="request-title">
        <div class="content-shell lead-layout">
          <div class="lead-copy">
            <p class="section-index">07 / Заявка</p>
            <h2 id="request-title">Коротко опишите проблему</h2>
            <p>Менеджер уточнит детали в течение 2 рабочих часов. Все работы выполняем удалённо. Для первого обращения достаточно контакта и краткого описания проблемы.</p>
          </div>

          <form class="lead-form" novalidate data-lead-form autocomplete="on">
            <div class="form-honey" aria-hidden="true">
              <label for="website">Не заполняйте это поле</label>
              <input id="website" name="_honey" type="text" tabindex="-1" autocomplete="off">
            </div>
            <fieldset class="contact-choice">
              <legend>Как с вами связаться? <span aria-hidden="true">*</span></legend>
              <label><input type="radio" name="contact_type" value="phone" checked> Телефон</label>
              <label><input type="radio" name="contact_type" value="email"> Email</label>
            </fieldset>

            <div class="form-field" data-contact-field="phone">
              <label for="phone">Телефон <span aria-hidden="true">*</span></label>
              <input id="phone" name="phone" type="tel" inputmode="tel" autocomplete="tel" placeholder="+7 900 000-00-00" aria-describedby="phone-error">
              <p class="field-error" id="phone-error"></p>
            </div>

            <div class="form-field" data-contact-field="email" hidden>
              <label for="email">Email <span aria-hidden="true">*</span></label>
              <input id="email" name="email" type="email" inputmode="email" autocomplete="email" placeholder="name@company.ru" aria-describedby="email-error" disabled>
              <p class="field-error" id="email-error"></p>
            </div>

            <div class="form-row">
              <div class="form-field">
                <label for="name">Имя <span>необязательно</span></label>
                <input id="name" name="name" type="text" autocomplete="name" maxlength="80">
              </div>
              <div class="form-field">
                <label for="company">Компания <span>необязательно</span></label>
                <input id="company" name="company" type="text" autocomplete="organization" maxlength="120">
              </div>
            </div>

            <div class="form-field">
              <label for="problem">Что происходит? <span aria-hidden="true">*</span></label>
              <textarea id="problem" name="problem" rows="5" maxlength="1500" placeholder="Например: ЭТрН формируется, но не уходит оператору ЭДО…" aria-describedby="problem-hint problem-error"></textarea>
              <p class="field-hint" id="problem-hint">Не указывайте пароли, закрытые ключи и персональные данные сотрудников.</p>
              <p class="field-error" id="problem-error"></p>
            </div>

            <section class="form-documents" aria-labelledby="form-documents-title">
              <h3 id="form-documents-title">Документы к заявке</h3>
              <p>Ознакомьтесь с условиями до отправки. Документы откроются в новой вкладке — заполненная форма сохранится.</p>
              <a class="document-link" href="assets/documents/offer.pdf?v=20260923" target="_blank" rel="noopener" aria-label="Публичная оферта — PDF, в новой вкладке">
                <span class="document-link__icon" aria-hidden="true"><svg viewBox="0 0 24 24" focusable="false"><path d="M7 3h7l4 4v14H7zM14 3v5h4M10 12h5M10 16h5"/></svg></span>
                <span class="document-link__label">Публичная оферта</span>
                <span class="document-link__format" aria-hidden="true">PDF</span>
                {CTA_ICON}
              </a>
              <a class="document-link" href="assets/documents/confidentiality.pdf?v=20260923" target="_blank" rel="noopener" aria-label="Соглашение о конфиденциальности — PDF, в новой вкладке">
                <span class="document-link__icon" aria-hidden="true"><svg viewBox="0 0 24 24" focusable="false"><path d="M12 3 4 6v6c0 4 4 7 8 9 4-2 8-5 8-9V6zM8 12l3 3 5-6"/></svg></span>
                <span class="document-link__label">Соглашение о конфиденциальности</span>
                <span class="document-link__format" aria-hidden="true">PDF</span>
                {CTA_ICON}
              </a>
            </section>

            <div class="consent-row">
              <input id="consent" name="consent" type="checkbox" aria-describedby="consent-error">
              <label for="consent">{'Согласен на обработку и передачу данных через FormSubmit для ответа на обращение.' if preview else 'Согласен на обработку персональных данных для ответа на обращение.'}</label>
              {consent_link}
            </div>
            <p class="field-error" id="consent-error"></p>

            <button class="button button--primary form-submit" type="submit">Отправить заявку {CTA_ICON}</button>
            <div class="form-status" data-form-status role="status" aria-live="polite"></div>
            <noscript><p>Для отправки формы включите JavaScript или напишите на <a href="mailto:{e(contacts['email'])}">{e(contacts['email'])}</a>.</p></noscript>
          </form>
        </div>
      </section>
    </main>

    <aside class="selection-toast" data-selection-toast role="status" aria-live="polite" hidden>
      <div>
        <strong>Добавлено в заявку</strong>
        <span data-selection-toast-text></span>
      </div>
      <a href="#request" data-cta data-placement="symptom_toast">Перейти к форме</a>
      <button type="button" data-selection-toast-close aria-label="Закрыть уведомление">×</button>
    </aside>

    <footer class="site-footer">
      <div class="content-shell footer-grid">
        <div class="footer-brand">
          <span class="brand__mark" aria-hidden="true"><img src="assets/aib-logo.png" alt="" width="100" height="66"></span>
          <div><strong>{e(company['public_name'])}</strong><span>{e(company['legal_name'])}</span></div>
        </div>
        <dl class="footer-contacts">
          <div><dt>Телефон</dt><dd><a href="tel:{e(contacts['phone_href'])}" data-contact data-channel="phone">{e(contacts['phone'])}</a></dd></div>
          <div><dt>Email</dt><dd><a href="mailto:{e(contacts['email'])}" data-contact data-channel="email">{e(contacts['email'])}</a></dd></div>
          <div><dt>Канал заявок</dt><dd>{e(contacts['delivery_channel'])}</dd></div>
        </dl>
        <div class="footer-docs">
          {offer_link}
          <a href="assets/documents/confidentiality.pdf?v=20260923" target="_blank" rel="noopener">Соглашение о конфиденциальности · PDF</a>
          {privacy_link}
          {'' if production else '<span>Предпросмотр · не для индексации</span>'}
        </div>
      </div>
    </footer>

    {render_draft_dialogs(preview) if not production else ''}
  </body>
</html>"""


def render_draft_dialogs(preview=True):
    company = config['company']
    contacts = config['contacts']
    form_config = config['form']
    return f"""<dialog class="info-dialog" id="privacy-dialog" aria-labelledby="privacy-title">
      <form method="dialog">
        <button class="dialog-close" aria-label="Закрыть окно">×</button>
        <p class="section-index">Проект документа</p>
        <h2 id="privacy-title">Обработка персональных данных</h2>
        <p>{e(company['legal_name'])} получает указанные в форме контакт, имя, компанию и описание проблемы для ответа на обращение. {'Передача выполняется через FormSubmit; сервис указывает хранение обращений до 30 дней.' if preview else 'Заявка сохраняется на сервере и отправляется на корпоративную почту через SMTP. Содержимое удаляется из очереди после приёма письма SMTP-сервером; недоставленные заявки хранятся до 7 дней.'} Не указывайте пароли, закрытые ключи и данные третьих лиц. Обратиться по вопросам обработки данных можно на {e(contacts['email'])}. Это проект условий для проверки настройки; финальные документы подключаются отдельно.</p>
        <button class="button button--dark" value="close">Понятно</button>
      </form>
    </dialog>

    """
