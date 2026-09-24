<?php
declare(strict_types=1);

// Deploys our files into an EXISTING licensed Bitrix site. Never writes /bitrix/.
if (PHP_SAPI !== 'cli') { http_response_code(403); exit('CLI only'); }
if (PHP_MAJOR_VERSION !== 8 || PHP_MINOR_VERSION !== 3) { fwrite(STDERR, "Запустите установщик через PHP 8.3 CLI.\n"); exit(1); }
define('B_PROLOG_INCLUDED', true);
require __DIR__ . '/site/local/templates/aib_etrn/lib/settings.php';

function ask(string $label, string $default = ''): string
{
    echo $label . ($default !== '' ? ' [' . $default . ']' : '') . ': ';
    $line = fgets(STDIN);
    if ($line === false) { throw new RuntimeException('Ввод прерван; установка остановлена.'); }
    $value = trim($line);
    return $value === '' ? $default : $value;
}

function protectedTarget(string $root, string $relative): string
{
    if (str_contains($relative, '..') || str_starts_with($relative, '/') || str_contains($relative, '\\')) {
        throw new RuntimeException('Недопустимый относительный путь');
    }
    $path = $root;
    foreach (explode('/', $relative) as $part) {
        $path .= '/' . $part;
        if (is_link($path)) { throw new RuntimeException('Отказ от записи через символическую ссылку: ' . $path); }
    }
    return $path;
}

function atomicFile(string $path, string $contents, int $mode): void
{
    $directory = dirname($path);
    if (!is_dir($directory) && !mkdir($directory, 0755, true)) { throw new RuntimeException('Не удалось создать каталог: ' . $directory); }
    $temporary = tempnam($directory, '.aib-');
    if ($temporary === false) { throw new RuntimeException('Не удалось создать временный файл'); }
    try {
        if (file_put_contents($temporary, $contents) !== strlen($contents) || !chmod($temporary, $mode) || !rename($temporary, $path)) {
            throw new RuntimeException('Не удалось сохранить: ' . $path);
        }
    } finally {
        if (is_file($temporary)) { unlink($temporary); }
    }
}

try {
    $args = getopt('', ['root:', 'backup-dir:', 'analytics-only', 'help']);
    if (isset($args['help'])) {
        echo "php bitrix/install.php --root=/home/www/site [--backup-dir=/private/backups] [--analytics-only]\n";
        exit(0);
    }
    $root = realpath((string)($args['root'] ?? ''));
    if (!$root || !isset($args['root']) || dirname($root) === $root) { throw new RuntimeException('Укажите существующий DOCUMENT_ROOT через --root'); }
    $root = str_replace('\\', '/', $root);
    foreach (['bitrix/header.php', 'bitrix/footer.php', 'bitrix/modules/main/include/prolog_before.php',
              'bitrix/components/bitrix/form.result.new/component.php'] as $required) {
        if (!is_file($root . '/' . $required)) { throw new RuntimeException('Не найдена установленная CMS/компонент: ' . $required); }
    }
    $configRelative = 'local/php_interface/aib_etrn.php';
    $configPath = protectedTarget($root, $configRelative);
    $old = is_file($configPath) ? require $configPath : [];
    if (!is_array($old)) { throw new RuntimeException('Конфигурация должна возвращать массив'); }
    $settings = \Aib\Etrn\validateSettings($old);
    $analyticsOnly = isset($args['analytics-only']);
    if ($analyticsOnly && !is_file($configPath)) { throw new RuntimeException('Сначала выполните полную установку'); }
    echo "Шаблон Компания АиБ. PHP 8.3 / 1С-Битрикс. Ядро и компонент не изменяются.\n";
    if (!$analyticsOnly) {
        do {
            $domain = ask('Домен сайта без https:// и пути', (string)parse_url($settings['site_url'], PHP_URL_HOST));
            $valid = (bool)preg_match('/^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,63}$/D', $domain);
            if (!$valid) { echo "Укажите доменное имя в ASCII/Punycode.\n"; }
        } while (!$valid);
        $settings['site_url'] = 'https://' . strtolower($domain);
        do {
            $formId = ask('ID существующей веб-формы Битрикса', $settings['form_id'] > 0 ? (string)$settings['form_id'] : '');
        } while (!ctype_digit($formId) || (int)$formId < 1);
        $settings['form_id'] = (int)$formId;
        foreach (['privacy_url' => 'Ссылка на политику', 'consent_url' => 'Ссылка на текст согласия'] as $key => $label) {
            do {
                $value = ask($label . ' (HTTPS или /путь, Enter — оставить/пропустить)', $settings[$key]);
            } while ($value !== '' && !\Aib\Etrn\validUrl($value));
            $settings[$key] = $value;
        }
        do {
            $mode = ask('Режим сайта: staging до приёмки, production после проверки формы/документов', $settings['environment']);
        } while (!in_array($mode, ['staging', 'production'], true));
        $settings['environment'] = $mode;
    }
    do {
        $metrica = ask('ID Метрики — необязательно (Enter — оставить/пропустить, - — отключить)', $settings['metrica_id']);
        if ($metrica === '-') { $metrica = ''; }
    } while ($metrica !== '' && !preg_match('/^[0-9]{5,12}$/D', $metrica));
    $settings['metrica_id'] = $metrica;
    $settings = \Aib\Etrn\validateSettings($settings);

    $files = [];
    if (!$analyticsOnly) {
        $source = realpath(__DIR__ . '/site');
        $iterator = new RecursiveIteratorIterator(new RecursiveDirectoryIterator($source, FilesystemIterator::SKIP_DOTS));
        foreach ($iterator as $file) {
            if ($file->isLink() || !$file->isFile()) { throw new RuntimeException('Пакет должен содержать только обычные файлы'); }
            $relative = str_replace('\\', '/', substr($file->getPathname(), strlen($source) + 1));
            if (str_starts_with($relative, 'bitrix/')) { throw new RuntimeException('Запрещено обновлять ядро'); }
            $files[$relative] = file_get_contents($file->getPathname());
        }
        if ($settings['environment'] !== 'production') { $files['robots.txt'] = file_get_contents(__DIR__ . '/robots.staging.txt'); }
    }
    $files[$configRelative] = "<?php\nif (!defined('B_PROLOG_INCLUDED') || B_PROLOG_INCLUDED !== true) { die(); }\nreturn " . var_export($settings, true) . ";\n";
    foreach ($files as $relative => $contents) {
        $target = protectedTarget($root, $relative);
        if ($contents === false || (file_exists($target) && !is_file($target))) { throw new RuntimeException('Необычный тип файла: ' . $relative); }
    }
    // The backup directory MUST be outside the web root and already exist.
    $backupBase = realpath((string)($args['backup-dir'] ?? dirname($root)));
    $backupBase = $backupBase ? str_replace('\\', '/', $backupBase) : '';
    if ($backupBase === '' || $backupBase === $root || str_starts_with($backupBase . '/', $root . '/')) {
        throw new RuntimeException('Каталог резервных копий должен существовать и находиться вне DOCUMENT_ROOT');
    }
    echo 'Будут установлены ' . count($files) . ' файлов в ' . $root . ".\n";
    echo "Существующие index.php, robots.txt, шаблон и включаемые области будут заменены с резервной копией.\n";
    if (strtolower(ask('Продолжить? Введите yes', 'no')) !== 'yes') { echo "Отменено, файлы не изменены.\n"; exit(0); }
    $backup = $backupBase . '/aib-etrn-backup-' . gmdate('Ymd-His') . '-' . bin2hex(random_bytes(4));
    if (!mkdir($backup, 0700)) { throw new RuntimeException('Нет прав на создание резервной копии'); }
    $manifest = ['root' => $root, 'replaced' => [], 'created' => []];
    foreach ($files as $relative => $contents) {
        $target = protectedTarget($root, $relative);
        if (is_file($target)) {
            atomicFile($backup . '/' . $relative, file_get_contents($target), 0600);
            $manifest['replaced'][] = $relative;
        } else { $manifest['created'][] = $relative; }
    }
    atomicFile($backup . '/manifest.json', json_encode($manifest, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_THROW_ON_ERROR), 0600);
    echo 'Резервная копия: ' . $backup . "\n";
    foreach ($files as $relative => $contents) {
        atomicFile(protectedTarget($root, $relative), $contents, 0644);
    }
    echo $analyticsOnly ? "Метрика обновлена. Сбросьте кеш/OPcache при необходимости.\n" : "Файлы установлены. Назначьте шаблон aib_etrn сайту в панели Битрикса.\n";
    echo $settings['environment'] === 'production' && $settings['metrica_id'] !== ''
        ? "Метрика включена. Проверьте счётчик в браузере.\n" : "Метрика не загружается (пустой ID или staging).\n";
    echo "База, веб-форма и почта CMS не менялись. Проверьте настройки и реальную заявку по README.\n";
} catch (Throwable $error) {
    fwrite(STDERR, 'Ошибка: ' . $error->getMessage() . "\n");
    exit(1);
}
