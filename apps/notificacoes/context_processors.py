"""Contador de notificações disponível em todas as telas autenticadas."""
from apps.notificacoes.models import NotificacaoSistema


def notificacoes_nao_lidas(request):
    if not request.user.is_authenticated:
        return {}
    return {
        "notificacoes_nao_lidas": NotificacaoSistema.objects.filter(
            usuario=request.user, lida_em__isnull=True
        ).count()
    }
