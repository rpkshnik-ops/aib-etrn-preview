<?php
namespace Aib\Etrn;

if (!defined('B_PROLOG_INCLUDED') || B_PROLOG_INCLUDED !== true) { die(); }

function defaults(): array
{
    return [
        'environment' => 'staging',
        'site_url' => '',
        'form_id' => 0,
        'metrica_id' => '',
        'privacy_url' => '',
        'consent_url' => '',
        'offer_url' => '/upload/aib-etrn/documents/offer.pdf',
        'confidentiality_url' => '/upload/aib-etrn/documents/confidentiality.pdf',
        'field_sids' => ['contact' => 'CONTACT', 'name' => 'NAME', 'company' => 'COMPANY',
                         'problem' => 'PROBLEM', 'consent' => 'CONSENT'],
    ];
}

function validUrl(string $value, bool $absolute = false): bool
{
    if (!$absolute && preg_match('~^/(?!/)[A-Za-z0-9/_.,%\-]+$~D', $value)) { return true; }
    $url = parse_url($value);
    return filter_var($value, FILTER_VALIDATE_URL) !== false && is_array($url)
        && ($url['scheme'] ?? '') === 'https'
        && !isset($url['user']) && !isset($url['pass'])
        && !isset($url['query']) && !isset($url['fragment']);
}

function validateSettings(array $values): array
{
    $data = array_replace(defaults(), $values);
    if (!in_array($data['environment'], ['staging', 'production'], true)) {
        throw new \InvalidArgumentException('environment: staging или production');
    }
    if (!is_int($data['form_id']) || $data['form_id'] < 0) {
        throw new \InvalidArgumentException('form_id: целочисленный ID веб-формы');
    }
    if (!is_string($data['metrica_id']) || ($data['metrica_id'] !== '' && !preg_match('/^[0-9]{5,12}$/D', $data['metrica_id']))) {
        throw new \InvalidArgumentException('metrica_id: 5–12 цифр или пустая строка');
    }
    foreach (['site_url', 'privacy_url', 'consent_url', 'offer_url', 'confidentiality_url'] as $key) {
        if (!is_string($data[$key]) || ($data[$key] !== '' && !validUrl($data[$key], $key === 'site_url'))) {
            throw new \InvalidArgumentException($key . ': ожидается HTTPS URL или путь от корня сайта');
        }
    }
    if ($data['site_url'] !== '' && !in_array(parse_url($data['site_url'], PHP_URL_PATH), [null, '', '/'], true)) {
        throw new \InvalidArgumentException('site_url: укажите домен без подкаталога');
    }
    $data['site_url'] = rtrim($data['site_url'], '/');
    if (!is_array($data['field_sids'])) { throw new \InvalidArgumentException('field_sids: массив символьных кодов вопросов'); }
    foreach (defaults()['field_sids'] as $role => $default) {
        if (!isset($data['field_sids'][$role]) || !is_string($data['field_sids'][$role])
            || !preg_match('/^[A-Za-z][A-Za-z0-9_]*$/D', $data['field_sids'][$role])) {
            throw new \InvalidArgumentException('Некорректный SID вопроса: ' . $role);
        }
    }
    if ($data['environment'] === 'production'
        && (!$data['site_url'] || !$data['form_id'] || !$data['privacy_url'] || !$data['consent_url'])) {
        throw new \InvalidArgumentException('Для production нужны домен, ID формы, политика и согласие');
    }
    return $data;
}

function settings(): array
{
    static $cached;
    if ($cached === null) {
        $path = $_SERVER['DOCUMENT_ROOT'] . '/local/php_interface/aib_etrn.php';
        $values = is_file($path) ? require $path : [];
        $cached = validateSettings(is_array($values) ? $values : []);
    }
    return $cached;
}

function h(mixed $value): string
{
    return htmlspecialchars((string)$value, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}

function documentUrl(string $key): string
{
    return h(settings()[$key] ?? '');
}
