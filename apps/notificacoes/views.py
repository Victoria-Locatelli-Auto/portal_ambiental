"""Central de notificações do usuário autenticado."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.notificacoes.models import NotificacaoSistema


@login_required
def lista(request: HttpRequest) -> HttpResponse:
    notificacoes = (
        NotificacaoSistema.objects.filter(usuario=request.user)
        .select_related("unidade", "documento", "documento__tipo")[:100]
    )
    return render(
        request,
        "notificacoes/lista.html",
        {"notificacoes": notificacoes, "secao": "notificacoes"},
    )


@login_required
def abrir(request: HttpRequest, uuid) -> HttpResponse:
    notificacao = get_object_or_404(NotificacaoSistema, uuid=uuid, usuario=request.user)
    if not notificacao.lida_em:
        notificacao.lida_em = timezone.now()
        notificacao.save(update_fields=["lida_em", "atualizado_em"])
    if notificacao.link and notificacao.link.startswith("/") and not notificacao.link.startswith("//"):
        return redirect(notificacao.link)
    raise Http404("O destino desta notificação não está disponível.")


@login_required
def marcar_todas_lidas(request: HttpRequest) -> HttpResponse:
    if request.method != "POST":
        raise Http404
    total = NotificacaoSistema.objects.filter(
        usuario=request.user, lida_em__isnull=True
    ).update(lida_em=timezone.now())
    messages.success(request, f"{total} notificação(ões) marcada(s) como lida(s).")
    return redirect("notificacoes:lista")
