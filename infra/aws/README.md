# AWS Entegrasyonu

Bu dizin AWS servis konfigürasyonlarını içerir.

## Planlanan İçerik

```
infra/aws/
├── README.md           # Bu dosya
├── s3.py               # S3 storage backend
├── cloudwatch.py       # CloudWatch logging
├── secrets.py          # Secrets Manager
├── ses.py              # Simple Email Service
└── iam/
    └── policies/       # IAM policy templates
```

## S3 Storage

Django'da S3 kullanımı için:

```python
# settings.py
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
STATICFILES_STORAGE = 'storages.backends.s3boto3.S3StaticStorage'

AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = config('AWS_STORAGE_BUCKET_NAME')
AWS_S3_REGION_NAME = config('AWS_S3_REGION_NAME', default='eu-central-1')
```

## CloudWatch Logging

```python
# CloudWatch handler örneği
LOGGING = {
    'handlers': {
        'cloudwatch': {
            'class': 'watchtower.CloudWatchLogHandler',
            'log_group': 'globalmain',
            'stream_name': 'django',
            'boto3_session': boto3.Session(
                aws_access_key_id=AWS_ACCESS_KEY_ID,
                aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                region_name=AWS_S3_REGION_NAME,
            ),
        },
    },
}
```

## Gerekli Paketler

```bash
pip install boto3
pip install django-storages
pip install watchtower  # CloudWatch logging
```

## TODO

- [ ] S3 storage backend implementasyonu
- [ ] CloudWatch logging entegrasyonu
- [ ] Secrets Manager entegrasyonu
- [ ] IAM policy templates
- [ ] SES email entegrasyonu

