<?php
// Test double for rendering the template contract, NOT a Bitrix implementation.
// Never deploy tests/. It neither validates nor stores real form submissions.
namespace Bitrix\Main\Page {
    class Asset {
        public array $scripts = [];
        public static function getInstance(): self { static $instance; return $instance ??= new self(); }
        public function addJs($path): void { $this->scripts[] = $path; }
    }
}
namespace Bitrix\Main {
    class Loader { public static function includeModule($module): bool { return $module === 'form'; } }
}
namespace {
    if (PHP_SAPI !== 'cli' && PHP_SAPI !== 'cli-server') { http_response_code(403); exit; }
    error_reporting(E_ALL);
    set_error_handler(static function ($level, $message, $file, $line) { throw new \ErrorException($message, 0, $level, $file, $line); });
    define('B_PROLOG_INCLUDED', true);
    define('LANGUAGE_ID', 'ru');
    define('SITE_TEMPLATE_PATH', '/local/templates/aib_etrn');
    $root = getenv('AIB_FIXTURE_ROOT') ?: dirname(__DIR__, 2) . '/bitrix/site';
    $_SERVER['DOCUMENT_ROOT'] = $root;
    $case = PHP_SAPI === 'cli' ? ($argv[1] ?? 'base') : ($_GET['case'] ?? 'base');
    if (PHP_SAPI === 'cli-server') {
        $uri = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);
        if (str_starts_with($uri, SITE_TEMPLATE_PATH . '/assets/') || str_starts_with($uri, '/upload/aib-etrn/documents/')
            || $uri === SITE_TEMPLATE_PATH . '/template_styles.css') {
            $file = realpath($root . $uri);
            $base = realpath($root);
            if (!$file || !str_starts_with($file, $base . DIRECTORY_SEPARATOR)) { http_response_code(404); exit; }
            $type = ['css' => 'text/css', 'js' => 'application/javascript', 'png' => 'image/png', 'pdf' => 'application/pdf'][pathinfo($file, PATHINFO_EXTENSION)] ?? '';
            if ($type === '') { http_response_code(404); exit; }
            header('Content-Type: ' . $type);
            readfile($file); exit;
        }
        if ($uri === '/bitrix/tools/captcha.php') { header('Content-Type: image/png'); readfile($root . SITE_TEMPLATE_PATH . '/assets/aib-logo.png'); exit; }
        if ($_SERVER['REQUEST_METHOD'] === 'POST') {
            header('Content-Type: application/json');
            echo json_encode(['fixture_only' => true, 'post' => $_POST], JSON_UNESCAPED_UNICODE); exit;
        }
    }
    require_once $root . SITE_TEMPLATE_PATH . '/lib/settings.php';

    class FixtureApplication {
        public function SetPageProperty($key, $value): void {}
        public function ShowHead(): void {
            echo '<meta charset="utf-8"><link rel="stylesheet" href="' . SITE_TEMPLATE_PATH . '/template_styles.css">';
            foreach (\Bitrix\Main\Page\Asset::getInstance()->scripts as $script) { echo '<script src="' . $script . '"></script>'; }
        }
        public function ShowTitle($browser = true): void { echo $browser ? 'Компания АиБ' : 'Поможем решить проблему с ЭТрН'; }
        public function ShowPanel(): void { echo '<div data-fixture-panel>Панель Битрикса — тестовая заглушка</div>'; }
        public function GetCurPage($index = true): string { return '/'; }
        public function IncludeFile($file, $params = [], $options = []): void { global $APPLICATION, $USER; include $_SERVER['DOCUMENT_ROOT'] . $file; }
        public function IncludeComponent($component, $template, $params, $parent): void {
            global $APPLICATION, $case;
            if ($component !== 'bitrix:form.result.new' || $template !== 'aib_etrn') { throw new \RuntimeException('Unexpected component'); }
            $arParams = $params;
            $arResult = fixtureResult($case);
            include $_SERVER['DOCUMENT_ROOT'] . SITE_TEMPLATE_PATH . '/components/bitrix/form.result.new/aib_etrn/template.php';
        }
    }
    function fixtureResult(string $case): array {
        $question = static fn($caption, $type, $html, $required = 'N') => [
            'CAPTION' => $caption, 'IS_HTML_CAPTION' => 'N', 'REQUIRED' => $required,
            'STRUCTURE' => [['FIELD_TYPE' => $type]], 'HTML_CODE' => $html,
        ];
        return [
            'FORM_HEADER' => '<form name="AIB_ETRN" action="/#request" method="post" enctype="multipart/form-data"><input type="hidden" name="WEB_FORM_ID" value="7"><input type="hidden" name="sessid" value="fixture-session-token">',
            'FORM_FOOTER' => '</form>', 'isFormErrors' => $case === 'errors' ? 'Y' : 'N',
            'FORM_ERRORS' => $case === 'errors' ? ['PROBLEM' => '<script>unsafe()</script>Заполните описание'] : [],
            'isFormNote' => $case === 'success' ? 'Y' : 'N', 'FORM_NOTE' => 'Спасибо, результат сохранён.',
            'F_RIGHT' => $case === 'denied' ? 0 : 10,
            'isUseCaptcha' => $case === 'captcha' ? 'Y' : 'N', 'CAPTCHACode' => 'fixture-captcha',
            'QUESTIONS' => [
                'CONTACT' => $question('Телефон или email', 'text', '<input type="text" name="form_text_101" value="' . ($case === 'errors' ? 'saved@example.org' : '') . '" maxlength="254" required>', 'Y'),
                'NAME' => $question('Имя', 'text', '<input type="text" name="form_text_102" value="" maxlength="80">'),
                'COMPANY' => $question('Компания', 'text', '<input type="text" name="form_text_103" value="" maxlength="120">'),
                'PROBLEM' => $question('Что происходит?', 'textarea', '<textarea name="form_textarea_104" rows="5" maxlength="1500" required>' . ($case === 'errors' ? 'Сохранённое описание' : '') . '</textarea>', 'Y'),
                'CONSENT' => $question('Согласие на обработку данных', 'checkbox', '<input type="checkbox" name="form_checkbox_CONSENT[]" value="105" id="fixture-consent"><label for="fixture-consent">Согласен на обработку данных для ответа на обращение</label>', 'Y'),
                'INTERNAL' => $question('Internal', 'hidden', '<input type="hidden" name="form_hidden_106" value="unchanged">'),
            ],
        ];
    }
    $APPLICATION = new FixtureApplication();
    $USER = new class { public function IsAdmin(): bool { return true; } };
    require $root . SITE_TEMPLATE_PATH . '/header.php';
    // Direct include of the real component template also works without an installed form ID.
    $APPLICATION->IncludeFile('/include/aib/landing.php');
    if (\Aib\Etrn\settings()['form_id'] === 0) {
        $arResult = fixtureResult($case);
        include $root . SITE_TEMPLATE_PATH . '/components/bitrix/form.result.new/aib_etrn/template.php';
    }
    require $root . SITE_TEMPLATE_PATH . '/footer.php';
}
