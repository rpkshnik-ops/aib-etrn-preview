<?php
if (!defined('B_PROLOG_INCLUDED') || B_PROLOG_INCLUDED !== true) { die(); }
?>
<section class="form-documents" aria-labelledby="form-documents-title">
              <h3 id="form-documents-title">Документы к заявке</h3>
              <p>Ознакомьтесь с условиями до отправки. Документы откроются в новой вкладке — заполненная форма сохранится.</p>
              <a class="document-link" href="<?= \Aib\Etrn\documentUrl('offer_url') ?>" target="_blank" rel="noopener" aria-label="Публичная оферта — PDF, в новой вкладке">
                <span class="document-link__icon" aria-hidden="true"><svg viewBox="0 0 24 24" focusable="false"><path d="M7 3h7l4 4v14H7zM14 3v5h4M10 12h5M10 16h5"/></svg></span>
                <span class="document-link__label">Публичная оферта</span>
                <span class="document-link__format" aria-hidden="true">PDF</span>
                <span class="button__icon" aria-hidden="true"><svg viewBox="0 0 20 20" focusable="false"><path d="M5 15 15 5M8 5h7v7"/></svg></span>
              </a>
              <a class="document-link" href="<?= \Aib\Etrn\documentUrl('confidentiality_url') ?>" target="_blank" rel="noopener" aria-label="Соглашение о конфиденциальности — PDF, в новой вкладке">
                <span class="document-link__icon" aria-hidden="true"><svg viewBox="0 0 24 24" focusable="false"><path d="M12 3 4 6v6c0 4 4 7 8 9 4-2 8-5 8-9V6zM8 12l3 3 5-6"/></svg></span>
                <span class="document-link__label">Соглашение о конфиденциальности</span>
                <span class="document-link__format" aria-hidden="true">PDF</span>
                <span class="button__icon" aria-hidden="true"><svg viewBox="0 0 20 20" focusable="false"><path d="M5 15 15 5M8 5h7v7"/></svg></span>
              </a>
            </section>
