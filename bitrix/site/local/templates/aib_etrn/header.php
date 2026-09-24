<?php
if (!defined('B_PROLOG_INCLUDED') || B_PROLOG_INCLUDED !== true) { die(); }
require_once __DIR__ . '/lib/settings.php';
$aibSettings = \Aib\Etrn\settings();
$APPLICATION->SetPageProperty('robots', $aibSettings['environment'] === 'production' ? 'index, follow' : 'noindex, nofollow');
\Bitrix\Main\Page\Asset::getInstance()->addJs(SITE_TEMPLATE_PATH . '/assets/ui.js');
?>
<!doctype html>
<html lang="<?= \Aib\Etrn\h(LANGUAGE_ID) ?>">
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="theme-color" content="#171914">
    <?php $APPLICATION->ShowHead(); ?>
    <title><?php $APPLICATION->ShowTitle(); ?></title>
    <meta property="og:type" content="website">
    <meta property="og:locale" content="ru_RU">
    <meta property="og:title" content="Компания АиБ — помощь с ЭТрН">
    <link rel="icon" href="<?= SITE_TEMPLATE_PATH ?>/assets/aib-logo.png" type="image/png">
    <?php if ($aibSettings['site_url'] !== ''): ?>
        <link rel="canonical" href="<?= \Aib\Etrn\h($aibSettings['site_url']) ?>/">
        <meta property="og:url" content="<?= \Aib\Etrn\h($aibSettings['site_url']) ?>/">
    <?php endif; ?>
</head>
<body class="aib-page" data-variant="b" data-form-mode="bitrix"
      data-analytics-counter="<?= $aibSettings['environment'] === 'production' ? \Aib\Etrn\h($aibSettings['metrica_id']) : '' ?>">
<div id="panel"><?php $APPLICATION->ShowPanel(); ?></div>
<div class="aib-landing">
<?php $APPLICATION->IncludeFile('/include/aib/header.php', [], ['MODE' => 'php', 'NAME' => 'Шапка лендинга']); ?>
<main id="main">
