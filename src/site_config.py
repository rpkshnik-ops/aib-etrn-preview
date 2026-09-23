SITE_CONFIG = {
    "company": {
        "public_name": "Компания АиБ",
        "legal_name": "ООО «Компания АиБ»",
        "public_name_approved": True,
        "inn": "6629004755",
        "kpp": "662901001",
        "ogrn": "1026601726470",
    },
    "service": {
        "short_name": "ЭТрН",
        "full_name": "электронные транспортные накладные",
        "price": 130000,
        "price_unit": "за одну согласованную заявку",
        "prepayment": "100% предоплата",
        "tax": "НДС — 5%",
        "headline": "Поможем решить проблему с ЭТрН",
        "summary": (
            "Диагностируем причину и устраняем согласованные ошибки обмена, "
            "подписания или передачи электронных транспортных накладных."
        ),
        "scope_note": (
            "Конкретную проблему, системы, объём работ и срок фиксируем "
            "в заявке до оплаты."
        ),
    },
    "contacts": {
        "email": "etrn@corp.aib.ru",
        "phone": "+7 961 777-02-20",
        "phone_href": "+79617770220",
        "delivery_channel": "Email",
        "publication_approved": True,
        "testing_only": True,
    },
    "form": {
        "provider": "FormSubmit",
        "endpoint": "https://formsubmit.co/ajax/etrn@corp.aib.ru",
        "recipient": "etrn@corp.aib.ru",
        "minimum_retry_seconds": 30,
        "duplicate_window_minutes": 10,
    },
    "analytics": {
        "provider": "Yandex Metrica",
        "counter_id": "",
        "enabled": False,
    },
    "promises": {
        "reply_within_two_hours": True,
        "same_day_diagnostics": False,
        "completion_in_one_to_five_days": True,
        "fourteen_day_guarantee": True,
        "unconditional_refund": False,
        "refund_terms_in_application": True,
        "epl_included": True,
        "all_edo_and_tms_included": True,
    },
    "symptoms": [
        {"title": "ЭТрН не отправляется", "text": "Документ не уходит в ЭДО или возвращается с ошибкой."},
        {"title": "Не получается подписать", "text": "Система не видит сертификат, полномочия или подпись."},
        {"title": "Документ завис", "text": "Статус не меняется при передаче между участниками обмена."},
        {"title": "Система формирует ошибку", "text": "Файл создаётся некорректно или не проходит проверку."},
        {"title": "Сбой после изменений", "text": "Обмен перестал работать после обновления или настройки."},
        {"title": "Причина непонятна", "text": "Нужно определить, на каком участке процесса возникла неполадка."},
    ],
}
