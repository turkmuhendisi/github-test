"""
Uluslararasılaştırma ve Yerelleştirme Ayarları (i18n/l10n)
==========================================================

Bu modül aşağıdaki ayarları içerir:
- Dil yapılandırması (LANGUAGES, LANGUAGE_CODE)
- Zaman dilimi (TIME_ZONE)
- Çeviri dosyaları (LOCALE_PATHS)
- Tarih/saat/sayı formatları

Terimler:
--------
- i18n: Internationalization (Uluslararasılaştırma)
- l10n: Localization (Yerelleştirme)

Notlar:
------
- Varsayılan dil: Türkçe (tr)
- Desteklenen diller: Türkçe, İngilizce
- Zaman dilimi: Europe/Istanbul (UTC+3)
"""

from django.utils.translation import gettext_lazy as _

from .env import BASE_DIR

# =============================================================================
# LANGUAGE SETTINGS
# =============================================================================
# https://docs.djangoproject.com/en/5.2/topics/i18n/

# Varsayılan dil kodu (ISO 639-1)
LANGUAGE_CODE = 'tr'

# Desteklenen diller (sıralama önemli - ilk sıra varsayılan)
# Format: (dil_kodu, görünen_isim)
LANGUAGES = [
    ('tr', _('Türkçe')),
    ('en', _('English')),
    # ('de', _('Deutsch')),
    # ('fr', _('Français')),
    # ('ar', _('العربية')),
    # ('ru', _('Русский')),
]

# Sadece dil kodları listesi (kullanım kolaylığı için)
LANGUAGE_CODES = [lang[0] for lang in LANGUAGES]

# =============================================================================
# INTERNATIONALIZATION (i18n)
# =============================================================================

# Django'nun çeviri sistemini aktifleştir
USE_I18N = True

# Yerel biçimlendirmeyi aktifleştir (tarih, sayı formatları)
USE_L10N = True

# =============================================================================
# LOCALE PATHS
# =============================================================================
# Çeviri dosyalarının (.po/.mo) konumu

LOCALE_PATHS = [
    BASE_DIR / 'locale',
    # Uygulama bazlı çeviri dizinleri otomatik taranır
    # ör: core/base/locale/, services/wallet/wallet/locale/
]

# =============================================================================
# TIME ZONE SETTINGS
# =============================================================================
# https://en.wikipedia.org/wiki/List_of_tz_database_time_zones

# Sunucu zaman dilimi
TIME_ZONE = 'Europe/Istanbul'

# Zaman dilimi farkındalığını aktifleştir
# True: Veritabanında UTC, görüntülemede local time
USE_TZ = True

# Alternatif zaman dilimleri:
# TIME_ZONE = 'UTC'
# TIME_ZONE = 'America/New_York'
# TIME_ZONE = 'Asia/Tokyo'
# TIME_ZONE = 'Europe/London'
# TIME_ZONE = 'Europe/Berlin'

# =============================================================================
# DATE/TIME FORMATS
# =============================================================================
# https://docs.djangoproject.com/en/5.2/ref/settings/#date-format

# Tarih formatı (USE_L10N=False olduğunda kullanılır)
DATE_FORMAT = 'd F Y'  # 25 Aralık 2025
SHORT_DATE_FORMAT = 'd.m.Y'  # 25.12.2025

# Saat formatı
TIME_FORMAT = 'H:i'  # 14:30
SHORT_TIME_FORMAT = 'H:i'  # 14:30

# Tarih-saat formatı
DATETIME_FORMAT = 'd F Y H:i'  # 25 Aralık 2025 14:30
SHORT_DATETIME_FORMAT = 'd.m.Y H:i'  # 25.12.2025 14:30

# Yıl-ay formatı
YEAR_MONTH_FORMAT = 'F Y'  # Aralık 2025
MONTH_DAY_FORMAT = 'd F'  # 25 Aralık

# =============================================================================
# NUMBER FORMATS
# =============================================================================
# Sayı formatları (USE_L10N=False olduğunda kullanılır)

# Ondalık ayırıcı
DECIMAL_SEPARATOR = ','

# Binlik ayırıcı
THOUSAND_SEPARATOR = '.'

# Binlik gruplandırma
NUMBER_GROUPING = 3

# Para birimi (özel kullanım için)
CURRENCY_SYMBOL = '₺'
CURRENCY_CODE = 'TRY'

# =============================================================================
# FIRST DAY OF WEEK
# =============================================================================
# Haftanın ilk günü (takvimler için)
# 0: Pazartesi, 6: Pazar

FIRST_DAY_OF_WEEK = 1  # Pazartesi (Türkiye için)
# FIRST_DAY_OF_WEEK = 0  # Pazar (ABD için)

# =============================================================================
# LANGUAGE COOKIE
# =============================================================================
# Kullanıcı dil tercihini saklamak için cookie

LANGUAGE_COOKIE_NAME = 'django_language'
LANGUAGE_COOKIE_AGE = 60 * 60 * 24 * 365  # 1 yıl
LANGUAGE_COOKIE_DOMAIN = None  # Tüm domain için
LANGUAGE_COOKIE_PATH = '/'
LANGUAGE_COOKIE_SECURE = False  # Production'da True
LANGUAGE_COOKIE_HTTPONLY = False  # JavaScript erişimi için False
LANGUAGE_COOKIE_SAMESITE = 'Lax'

# =============================================================================
# LANGUAGE DETECTION
# =============================================================================
# Dil tespit öncelik sırası (LocaleMiddleware):
# 1. URL prefix (/en/, /tr/)
# 2. Session
# 3. Cookie
# 4. Accept-Language header
# 5. LANGUAGE_CODE (varsayılan)

# URL prefix kullanımı (urls.py'da i18n_patterns gerektirir)
USE_I18N_URLS = True

# =============================================================================
# FORMAT LOCALIZATION
# =============================================================================
# Locale bazlı formatlar (USE_L10N=True olduğunda)

# Türkçe formatlar (otomatik uygulanır)
# Tarih: 25 Aralık 2025
# Saat: 14:30
# Sayı: 1.234.567,89

# =============================================================================
# TRANSLATION SETTINGS
# =============================================================================
# Çeviri davranış ayarları

# Eksik çevirilerde fallback dili
# LANGUAGE_CODE kullanılır

# Çeviri önbelleği (production'da aktif olmalı)
# USE_CACHED_TRANSLATIONS = True  # Django 4.2+

# =============================================================================
# PARLER SETTINGS (Opsiyonel - Model Çevirisi)
# =============================================================================
# pip install django-parler
# Veritabanındaki içeriklerin çevirisi için

# PARLER_LANGUAGES = {
#     None: (  # Global site
#         {'code': 'tr'},
#         {'code': 'en'},
#     ),
#     'default': {
#         'fallbacks': ['tr'],
#         'hide_untranslated': False,
#     }
# }

# PARLER_DEFAULT_LANGUAGE_CODE = 'tr'

# =============================================================================
# MODELTRANSLATION SETTINGS (Opsiyonel - Model Çevirisi)
# =============================================================================
# pip install django-modeltranslation

# MODELTRANSLATION_DEFAULT_LANGUAGE = 'tr'
# MODELTRANSLATION_LANGUAGES = ('tr', 'en')
# MODELTRANSLATION_FALLBACK_LANGUAGES = ('tr', 'en')
# MODELTRANSLATION_PREPOPULATE_LANGUAGE = 'tr'

# =============================================================================
# ROSETTA SETTINGS (Opsiyonel - Web Çeviri Arayüzü)
# =============================================================================
# pip install django-rosetta

# ROSETTA_MESSAGES_PER_PAGE = 50
# ROSETTA_ENABLE_TRANSLATION_SUGGESTIONS = True
# ROSETTA_SHOW_AT_ADMIN_PANEL = True
# ROSETTA_STORAGE_CLASS = 'rosetta.storage.CacheRosettaStorage'
# ROSETTA_CACHE_NAME = 'rosetta'

# =============================================================================
# CKEditor / TinyMCE i18n (Opsiyonel)
# =============================================================================
# Rich text editörler için dil ayarları

# CKEDITOR_CONFIGS = {
#     'default': {
#         'language': 'tr',
#     }
# }