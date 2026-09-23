import argparse
import re
from pathlib import Path

parser = argparse.ArgumentParser(description='Render an HTTP vhost; use Certbot for HTTPS')
parser.add_argument('--domain', required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
domain = args.domain.encode('idna').decode('ascii').lower()
if len(domain) > 253 or not re.fullmatch(r'(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}', domain):
    parser.error('Provide a domain name only, e.g. etrn.company.ru')
if 'your-domain' in domain:
    parser.error('Replace YOUR-DOMAIN with the actual domain')
template = Path(__file__).with_name('nginx.conf.template').read_text(encoding='utf-8')
args.output.write_text(template.replace('__DOMAIN__', domain), encoding='utf-8')
print(args.output)
