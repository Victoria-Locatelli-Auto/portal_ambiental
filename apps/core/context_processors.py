from django.conf import settings


def siga(request):  # noqa: ARG001
    return {"SIGA": settings.SIGA}
