<?php
// Copy to /local/php_interface/aib_etrn.php or use the CLI installer.
if (!defined('B_PROLOG_INCLUDED') || B_PROLOG_INCLUDED !== true) { die(); }
return [
    'environment' => 'staging',
    'site_url' => '',
    'form_id' => 0,
    'metrica_id' => '', // Optional. Empty means no analytics script or requests.
    'privacy_url' => '',
    'consent_url' => '',
    'field_sids' => ['contact' => 'CONTACT', 'name' => 'NAME', 'company' => 'COMPANY',
                     'problem' => 'PROBLEM', 'consent' => 'CONSENT'],
];
