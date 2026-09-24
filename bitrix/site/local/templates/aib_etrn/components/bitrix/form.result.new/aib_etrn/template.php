<?php
if (!defined('B_PROLOG_INCLUDED') || B_PROLOG_INCLUDED !== true) { die(); }
// Presentation only. The original component validates and stores the result.
require_once $_SERVER['DOCUMENT_ROOT'] . '/local/templates/aib_etrn/lib/settings.php';
$aibSettings = \Aib\Etrn\settings();
$roles = array_flip($aibSettings['field_sids']);
$hasErrors = ($arResult['isFormErrors'] ?? 'N') === 'Y';
$hasNote = ($arResult['isFormNote'] ?? 'N') === 'Y';
$plain = static fn($text): string => \Aib\Etrn\h(is_scalar($text) ? strip_tags((string)$text) : '');
?>
<?php if ($hasErrors): ?>
    <div class="aib-form-message aib-form-message--error" data-bitrix-errors role="alert" tabindex="-1">
        <strong>Проверьте заполнение формы</strong>
        <?php if (!empty($arResult['FORM_ERRORS']) && is_array($arResult['FORM_ERRORS'])): ?>
            <ul><?php foreach ($arResult['FORM_ERRORS'] as $error): ?><li><?= $plain($error) ?></li><?php endforeach; ?></ul>
        <?php else: ?>
            <p><?= $plain($arResult['FORM_ERRORS_TEXT'] ?? '') ?></p>
        <?php endif; ?>
    </div>
<?php endif; ?>
<?php if ($hasNote && !$hasErrors): ?>
    <div class="lead-form aib-form-success" data-bitrix-success role="status" tabindex="-1">
        <h3>Заявка принята</h3>
        <p><?= $plain($arResult['FORM_NOTE'] ?? '') ?></p>
        <p>Ответим в течение 2 рабочих часов.</p>
        <a class="button button--primary" href="<?= \Aib\Etrn\h($APPLICATION->GetCurPage(false)) ?>#request">Новая заявка</a>
    </div>
<?php else: ?>
    <div class="lead-form aib-bitrix-form" data-bitrix-form>
    <?= $arResult['FORM_HEADER'] ?? '' ?>
    <?php foreach (($arResult['QUESTIONS'] ?? []) as $sid => $question): ?>
        <?php
        $role = $roles[$sid] ?? '';
        $structure = $question['STRUCTURE'] ?? [];
        $types = array_column($structure, 'FIELD_TYPE');
        if ($types && count(array_filter($types, static fn($type) => $type !== 'hidden')) === 0) {
            echo $question['HTML_CODE']; // Includes the original names, values and component constraints.
            continue;
        }
        if ($role === 'consent') {
            $APPLICATION->IncludeFile('/include/aib/documents.php', [], ['MODE' => 'php', 'SHOW_BORDER' => false]);
        }
        $fieldError = $arResult['FORM_ERRORS'][$sid] ?? '';
        ?>
        <fieldset class="form-field aib-question <?= $role === 'consent' ? 'aib-question--consent' : '' ?>"
                  data-aib-field="<?= \Aib\Etrn\h($role) ?>" data-required="<?= ($question['REQUIRED'] ?? 'N') === 'Y' ? 'Y' : 'N' ?>">
            <legend>
                <?= ($question['IS_HTML_CAPTION'] ?? 'N') === 'Y' ? $question['CAPTION'] : \Aib\Etrn\h($question['CAPTION'] ?? $sid) ?>
                <?php if (($question['REQUIRED'] ?? 'N') === 'Y'): ?><span aria-hidden="true"> *</span><?php endif; ?>
            </legend>
            <div class="aib-question__control"><?= $question['HTML_CODE'] ?? '' ?></div>
            <?php if ($role === 'problem'): ?>
                <p class="field-hint">Не указывайте пароли, закрытые ключи и персональные данные сотрудников.</p>
            <?php elseif ($role === 'consent'): ?>
                <?php if ($aibSettings['consent_url'] !== ''): ?>
                    <a class="inline-link" href="<?= \Aib\Etrn\documentUrl('consent_url') ?>" target="_blank" rel="noopener">Текст согласия</a>
                <?php else: ?>
                    <p class="field-hint">Текст согласия готовится к публикации. До запуска используйте только собственные тестовые данные.</p>
                <?php endif; ?>
            <?php endif; ?>
            <?php if ($fieldError !== ''): ?><p class="field-error"><?= $plain($fieldError) ?></p><?php endif; ?>
        </fieldset>
    <?php endforeach; ?>
    <?php if (!isset($arResult['QUESTIONS'][$aibSettings['field_sids']['consent']])): ?>
        <?php $APPLICATION->IncludeFile('/include/aib/documents.php', [], ['MODE' => 'php', 'SHOW_BORDER' => false]); ?>
    <?php endif; ?>
    <?php if (($arResult['isUseCaptcha'] ?? 'N') === 'Y'): ?>
        <div class="form-field aib-captcha">
            <label for="aib-captcha-word">Введите символы с картинки <span aria-hidden="true">*</span></label>
            <input type="hidden" name="captcha_sid" value="<?= \Aib\Etrn\h($arResult['CAPTCHACode'] ?? '') ?>">
            <img src="/bitrix/tools/captcha.php?captcha_sid=<?= rawurlencode($arResult['CAPTCHACode'] ?? '') ?>" width="180" height="40" alt="Проверочный код CAPTCHA">
            <input type="text" name="captcha_word" id="aib-captcha-word" size="30" maxlength="50" autocomplete="off" required>
        </div>
    <?php endif; ?>
    <p class="field-hint">* — обязательные поля.</p>
    <button class="button button--primary form-submit" type="submit" name="web_form_submit" value="Отправить заявку"
            <?= isset($arResult['F_RIGHT']) && (int)$arResult['F_RIGHT'] < 10 ? 'disabled' : '' ?>>
        Отправить заявку <span class="button__icon" aria-hidden="true"><svg viewBox="0 0 20 20" focusable="false"><path d="M5 15 15 5M8 5h7v7"/></svg></span>
    </button>
    <div class="form-status" data-form-status role="status" aria-live="polite"></div>
    <?= $arResult['FORM_FOOTER'] ?? '' ?>
    </div>
<?php endif; ?>
