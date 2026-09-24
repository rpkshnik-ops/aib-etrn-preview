<?php
// A form with a session token/CAPTCHA must not be served from composite HTML cache.
define('BX_COMPOSITE_SKIP', true);
require $_SERVER['DOCUMENT_ROOT'] . '/bitrix/header.php';

$APPLICATION->SetTitle('Поможем решить проблему с ЭТрН');
$APPLICATION->SetPageProperty('title', 'Решение проблем с ЭТрН — 130 000 ₽ | Компания АиБ');
$APPLICATION->SetPageProperty('description', 'Удалённая диагностика и устранение согласованных проблем с ЭТрН, ЭПЛ, ЭДО, 1С и TMS. Одна заявка — 130 000 ₽, НДС 5%.');
$APPLICATION->IncludeFile('/include/aib/landing.php', [], ['MODE' => 'php', 'NAME' => 'Содержимое лендинга ЭТрН']);

require $_SERVER['DOCUMENT_ROOT'] . '/bitrix/footer.php';
