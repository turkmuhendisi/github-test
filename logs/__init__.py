"""
Logs Modülleri
==============

Log yönetimi, audit, analytics ve monitoring uygulamaları.

Alt Modüller:
------------
- viewer   : Log dosyası görüntüleyici (Web UI)
- audit    : Audit log sistemi (veritabanı)
- analytics: Log analizi ve dashboard
- utils    : Gelişmiş logging utilities

Veritabanı:
----------
audit ve activity modelleri 'logs' veritabanına yönlendirilir.
(tools.db.routers.LogsRouter tarafından)
"""

__version__ = "1.0.0"

