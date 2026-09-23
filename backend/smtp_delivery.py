"""SMTP transport with certificate verification and no credential/body logging."""
import re
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formatdate
from urllib.parse import urlsplit


class DeliveryError(Exception):
    pass


def validate_smtp(values):
    result = dict(values)
    host = result.get('host', '')
    if not isinstance(host, str) or not host or any(c.isspace() for c in host) or any(c in host for c in '/\\@'):
        raise ValueError('Укажите имя SMTP-сервера без протокола и пути')
    result['host'] = host.encode('idna').decode('ascii')
    if type(result.get('port')) is not int or not 1 <= result['port'] <= 65535:
        raise ValueError('SMTP-порт должен быть числом от 1 до 65535')
    if result.get('security') not in ('starttls', 'ssl'):
        raise ValueError('Режим SMTP: starttls или ssl')
    for key in ('username', 'password'):
        if not isinstance(result.get(key, ''), str) or '\x00' in result.get(key, '') or '\n' in result.get(key, '') or '\r' in result.get(key, ''):
            raise ValueError('Некорректный параметр SMTP: ' + key)
    result.setdefault('username', '')
    result.setdefault('password', '')
    if result['username'] and not result['password']:
        raise ValueError('Для SMTP-логина требуется пароль')
    sender = result.get('from_email', '')
    if not isinstance(sender, str) or not re.fullmatch(r'[^\s@<>]+@[^\s@<>]+\.[^\s@<>]+', sender):
        raise ValueError('Укажите корректный email отправителя')
    return result


def deliver(cfg, identifier, payload):
    smtp = validate_smtp(cfg['smtp'])
    message = EmailMessage()
    message['From'] = smtp['from_email']
    message['To'] = cfg['recipient']
    message['Subject'] = 'Заявка с лендинга «Компания АиБ»'
    message['Date'] = formatdate(localtime=False)
    message['Message-ID'] = f"<{identifier}@{urlsplit(cfg['origin']).hostname}>"
    if payload['contact_type'] == 'email':
        message['Reply-To'] = payload['contact']
    message.set_content('\n'.join([
        'Заявка с лендинга «Компания АиБ»', '',
        'Номер: ' + identifier,
        'Способ связи: ' + payload['contact_type'],
        'Контакт: ' + payload['contact'],
        'Имя: ' + payload['name'],
        'Компания: ' + payload['company'],
        '', 'Описание:', payload['problem'], '',
        'Согласие на обработку данных: получено в форме',
        'Страница: ' + payload['page_url'],
    ]))
    context = ssl.create_default_context()
    connection = None
    try:
        if smtp['security'] == 'ssl':
            connection = smtplib.SMTP_SSL(smtp['host'], smtp['port'], timeout=20, context=context)
        else:
            connection = smtplib.SMTP(smtp['host'], smtp['port'], timeout=20)
            connection.ehlo()
            connection.starttls(context=context)
            connection.ehlo()
        if smtp['username']:
            connection.login(smtp['username'], smtp['password'])
        refused = connection.send_message(message, from_addr=smtp['from_email'], to_addrs=[cfg['recipient']])
        if refused:
            raise DeliveryError('smtp_recipient_refused')
    except smtplib.SMTPAuthenticationError:
        raise DeliveryError('smtp_authentication_failed') from None
    except ssl.SSLCertVerificationError:
        raise DeliveryError('smtp_certificate_invalid') from None
    except smtplib.SMTPNotSupportedError:
        raise DeliveryError('smtp_tls_or_auth_not_supported') from None
    except smtplib.SMTPRecipientsRefused:
        raise DeliveryError('smtp_recipient_refused') from None
    except smtplib.SMTPResponseException as error:
        raise DeliveryError('smtp_response_' + str(error.smtp_code)) from None
    except UnicodeError:
        raise DeliveryError('smtp_credentials_or_address_encoding') from None
    except (OSError, smtplib.SMTPException):
        raise DeliveryError('smtp_unavailable') from None
    finally:
        if connection is not None:
            # An error on QUIT after DATA was accepted must not duplicate a message.
            try:
                connection.quit()
            except (OSError, smtplib.SMTPException):
                connection.close()
