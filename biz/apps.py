from django.apps import AppConfig

class BizConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'biz'
    verbose_name = '03. 业务中心'

    def ready(self):
        import biz.signals  # 必须写这行！