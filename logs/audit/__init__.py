"""
Audit Log App
=============

Kullanıcı aktivitelerini veritabanında kaydetme.

Özellikler:
----------
- User action tracking
- Model change history (created, updated, deleted)
- Login/logout logları
- IP ve device tracking

Veritabanı:
----------
Bu app 'logs' veritabanına yönlendirilir.
(tools.db.routers.LogsRouter tarafından)
"""

default_app_config = 'logs.audit.apps.AuditConfig'

