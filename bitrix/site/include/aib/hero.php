<?php
if (!defined('B_PROLOG_INCLUDED') || B_PROLOG_INCLUDED !== true) { die(); }
?>
      <section class="hero hero--final" id="top" aria-labelledby="hero-title">
        <div class="hero__glow hero__glow--one" aria-hidden="true"></div>
        <div class="hero__glow hero__glow--two" aria-hidden="true"></div>
        <div class="hero__grid">
          <div class="hero__copy">
            <p class="eyebrow"><span aria-hidden="true"></span> Техническая помощь для бизнеса</p>
            <h1 id="hero-title"><?php $APPLICATION->ShowTitle(false); ?></h1>
            <p class="hero__lead">Диагностируем причину и устраняем согласованные ошибки ЭТрН, ЭПЛ и электронного документооборота — от подписи до обмена между 1С, TMS и оператором ЭДО.</p>
            <div class="hero__actions">
              <a class="button button--primary" href="#request" data-cta data-placement="hero">Обсудить проблему <span class="button__icon" aria-hidden="true"><svg viewBox="0 0 20 20" focusable="false"><path d="M5 15 15 5M8 5h7v7"/></svg></span></a>
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
            <p class="price-panel__value">130 000<span> ₽</span></p>
            <p class="price-panel__unit">за одну согласованную заявку</p>
            <div class="price-panel__rule"></div>
            <p class="price-panel__prepay">100% предоплата · НДС — 5%</p>
            <p class="price-panel__note">Конкретную проблему, системы, объём работ и срок фиксируем в заявке до оплаты.</p>
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
