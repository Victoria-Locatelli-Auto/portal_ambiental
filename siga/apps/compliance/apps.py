from django.apps import AppConfig


class ComplianceConfig(AppConfig):
    name = "apps.compliance"
    verbose_name = "Conformidade legal"

    def ready(self) -> None:
        from apps.compliance import signals  # noqa: F401
