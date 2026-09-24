<?php
if (!defined('B_PROLOG_INCLUDED') || B_PROLOG_INCLUDED !== true) { die(); }
require_once $_SERVER['DOCUMENT_ROOT'] . '/local/templates/aib_etrn/lib/settings.php';
$aibSettings = \Aib\Etrn\settings();
?>
<section class="lead-section" id="request" aria-labelledby="request-title">
    <div class="content-shell lead-layout">
        <div class="lead-copy">
            <p class="section-index">07 / Заявка</p>
            <h2 id="request-title">Коротко опишите проблему</h2>
            <p>Менеджер уточнит детали в течение 2 рабочих часов. Все работы выполняем удалённо. Для первого обращения достаточно контакта и краткого описания проблемы.</p>
        </div>
        <div class="aib-form-container">
        <?php if ($aibSettings['form_id'] > 0 && \Bitrix\Main\Loader::includeModule('form')): ?>
            <?php $APPLICATION->IncludeComponent('bitrix:form.result.new', 'aib_etrn', [
                'WEB_FORM_ID' => $aibSettings['form_id'],
                'IGNORE_CUSTOM_TEMPLATE' => 'Y',
                'USE_EXTENDED_ERRORS' => 'Y',
                'SEF_MODE' => 'N',
                'VARIABLE_ALIASES' => ['WEB_FORM_ID' => 'WEB_FORM_ID', 'RESULT_ID' => 'RESULT_ID'],
                'CACHE_TYPE' => 'N',
                'CACHE_TIME' => '0',
                'AJAX_MODE' => 'N',
                'LIST_URL' => '',
                'EDIT_URL' => '',
                'SUCCESS_URL' => '',
                'CHAIN_ITEM_TEXT' => '',
                'CHAIN_ITEM_LINK' => '',
            ], false); ?>
        <?php else: ?>
            <div class="lead-form" role="status">
                <p>Форма временно недоступна. Свяжитесь с нами: <a href="mailto:etrn@corp.aib.ru">etrn@corp.aib.ru</a> или <a href="tel:+79617770220">+7 961 777-02-20</a>.</p>
                <?php if (isset($USER) && $USER->IsAdmin()): ?>
                    <p>Администратору: включите модуль «Веб-формы» и укажите form_id в /local/php_interface/aib_etrn.php.</p>
                <?php endif; ?>
            </div>
        <?php endif; ?>
        </div>
    </div>
</section>
