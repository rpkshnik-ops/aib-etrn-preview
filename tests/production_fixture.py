"""Synthetic browser fixture only; these document URLs are NOT real company documents."""
from pathlib import Path
from build import build

if __name__ == '__main__':
    build(Path('dist'), {
        'mode': 'production',
        'site_url': 'https://landing.example.org/',
        'privacy_url': 'https://landing.example.org/legal/privacy.pdf',
        'consent_url': 'https://landing.example.org/legal/consent.pdf',
        'offer_url': 'https://landing.example.org/legal/offer.pdf',
        'delivery_confirmed': True,
    })
