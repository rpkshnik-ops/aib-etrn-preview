<?php
if (!defined('B_PROLOG_INCLUDED') || B_PROLOG_INCLUDED !== true) { die(); }
?>


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
          <span class="brand__mark" aria-hidden="true"><img src="/local/templates/aib_etrn/assets/aib-logo.png" alt="" width="100" height="66"></span>
          <div><strong>Компания АиБ</strong><span>ООО «Компания АиБ»</span></div>
        </div>
        <dl class="footer-contacts">
          <div><dt>Телефон</dt><dd><a href="tel:+79617770220" data-contact data-channel="phone">+7 961 777-02-20</a></dd></div>
          <div><dt>Email</dt><dd><a href="mailto:etrn@corp.aib.ru" data-contact data-channel="email">etrn@corp.aib.ru</a></dd></div>
          <div><dt>Канал заявок</dt><dd>Email</dd></div>
        </dl>
        <div class="footer-docs">
          <a href="<?= \Aib\Etrn\documentUrl('offer_url') ?>" target="_blank" rel="noopener">Публичная оферта · PDF</a>
          <a href="<?= \Aib\Etrn\documentUrl('confidentiality_url') ?>" target="_blank" rel="noopener">Соглашение о конфиденциальности · PDF</a>
          <?php if (\Aib\Etrn\settings()['privacy_url'] !== ''): ?><a class="inline-link" href="<?= \Aib\Etrn\documentUrl('privacy_url') ?>" target="_blank" rel="noopener">Обработка данных</a><?php endif; ?>

        </div>
      </div>
    </footer>



