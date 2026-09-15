"""Área administrativa amigável, sem dependência da interface do Django Admin."""
from __future__ import annotations

from functools import wraps

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.mail import send_mail
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.forms import TipoDocumentoForm, UsuarioCriacaoForm, UsuarioEdicaoForm
from apps.accounts.models import Perfil
from apps.compliance.models import TipoDocumento
from apps.notificacoes.forms import EmailTesteForm, ModeloEmailForm
from apps.notificacoes.models import ModeloEmail

Usuario = get_user_model()


def admin_required(view):
    @wraps(view)
    @login_required
    def protegida(request: HttpRequest, *args, **kwargs):
        if request.user.perfil != Perfil.ADMIN:
            raise PermissionDenied("Somente administradores podem configurar o sistema.")
        return view(request, *args, **kwargs)

    return protegida


@admin_required
def inicio(request: HttpRequest) -> HttpResponse:
    return render(
        request,
        "accounts/admin/inicio.html",
        {
            "secao": "administracao",
            "total_tipos": TipoDocumento.objects.filter(ativo=True).count(),
            "total_usuarios": Usuario.objects.filter(is_active=True).count(),
            "total_inativos": Usuario.objects.filter(is_active=False).count(),
        },
    )


@admin_required
def tipos_documento(request: HttpRequest) -> HttpResponse:
    busca = request.GET.get("q", "").strip()
    tipos = TipoDocumento.objects.annotate(total_documentos=Count("documentos"))
    if busca:
        tipos = tipos.filter(Q(codigo__icontains=busca) | Q(nome__icontains=busca))
    return render(
        request,
        "accounts/admin/tipos_lista.html",
        {"secao": "tipos_documento", "tipos": tipos, "busca": busca},
    )


@admin_required
def tipo_criar(request: HttpRequest) -> HttpResponse:
    formulario = TipoDocumentoForm(request.POST or None)
    if formulario.is_valid():
        tipo = formulario.save()
        messages.success(request, f"Tipo documental {tipo.codigo} cadastrado com sucesso.")
        return redirect("administracao:tipos")
    return _render_formulario(
        request, formulario, "tipos_documento", "Novo tipo de documento",
        "", "administracao:tipos",
    )


@admin_required
def tipo_editar(request: HttpRequest, uuid) -> HttpResponse:
    tipo = get_object_or_404(TipoDocumento, uuid=uuid)
    formulario = TipoDocumentoForm(request.POST or None, instance=tipo)
    if formulario.is_valid():
        formulario.save()
        messages.success(request, f"Tipo documental {tipo.codigo} atualizado.")
        return redirect("administracao:tipos")
    return _render_formulario(
        request, formulario, "tipos_documento", f"Editar {tipo.codigo}", tipo.nome,
        "administracao:tipos",
    )


@admin_required
def tipo_alternar(request: HttpRequest, uuid) -> HttpResponse:
    tipo = get_object_or_404(TipoDocumento, uuid=uuid)
    if request.method == "POST":
        tipo.ativo = not tipo.ativo
        tipo.save(update_fields=["ativo", "atualizado_em"])
        estado = "reativado" if tipo.ativo else "desativado"
        messages.success(request, f"Tipo documental {tipo.codigo} {estado}.")
        return redirect("administracao:tipos")
    return render(
        request,
        "accounts/admin/confirmar.html",
        {
            "secao": "tipos_documento",
            "titulo": "Reativar tipo documental" if not tipo.ativo else "Desativar tipo documental",
            "objeto": f"{tipo.codigo} — {tipo.nome}",
            "aviso": (
                "O histórico será preservado. O item deixará de aparecer nos novos checklists."
                if tipo.ativo else "O item voltará a aparecer nos checklists aplicáveis."
            ),
            "voltar": "administracao:tipos",
            "acao": "Reativar" if not tipo.ativo else "Desativar",
        },
    )


@admin_required
def usuarios(request: HttpRequest) -> HttpResponse:
    busca = request.GET.get("q", "").strip()
    lista = Usuario.objects.select_related("unidade").all()
    if busca:
        lista = lista.filter(Q(nome_completo__icontains=busca) | Q(email__icontains=busca))
    return render(
        request,
        "accounts/admin/usuarios_lista.html",
        {"secao": "usuarios", "usuarios": lista, "busca": busca},
    )


@admin_required
def modelos_email(request: HttpRequest) -> HttpResponse:
    formulario_teste = EmailTesteForm(request.POST or None)
    if request.method == "POST" and formulario_teste.is_valid():
        destinatario = formulario_teste.cleaned_data["destinatario"]
        try:
            enviados = send_mail(
                "[SIGA-MCM] Teste da integração de e-mail",
                "Este é um e-mail de teste enviado pela configuração do SIGA.",
                settings.DEFAULT_FROM_EMAIL,
                [destinatario],
                fail_silently=False,
            )
        except Exception as erro:
            messages.error(request, f"Falha no envio: {erro}")
        else:
            if enviados:
                messages.success(request, f"E-mail de teste enviado para {destinatario}.")
            else:
                messages.warning(request, "O provedor não confirmou o envio do teste.")
            return redirect("administracao:modelos_email")
    return render(
        request,
        "accounts/admin/modelos_email.html",
        {
            "secao": "modelos_email",
            "modelos": ModeloEmail.objects.all(),
            "formulario_teste": formulario_teste,
            "remetente": settings.DEFAULT_FROM_EMAIL,
            "backend": settings.EMAIL_BACKEND,
        },
    )


@admin_required
def modelo_email_editar(request: HttpRequest, pk: int) -> HttpResponse:
    modelo = get_object_or_404(ModeloEmail, pk=pk)
    formulario = ModeloEmailForm(request.POST or None, instance=modelo)
    if formulario.is_valid():
        formulario.save()
        messages.success(request, f"Modelo {modelo.get_tipo_display()} atualizado.")
        return redirect("administracao:modelos_email")
    return render(
        request,
        "accounts/admin/modelo_email_form.html",
        {
            "secao": "modelos_email",
            "modelo": modelo,
            "formulario": formulario,
        },
    )


@admin_required
def usuario_criar(request: HttpRequest) -> HttpResponse:
    formulario = UsuarioCriacaoForm(request.POST or None)
    if formulario.is_valid():
        usuario = formulario.save()
        messages.success(request, f"Acesso de {usuario.nome_exibicao} criado com sucesso.")
        return redirect("administracao:usuarios")
    return _render_formulario(
        request, formulario, "usuarios", "Novo acesso",
        "Cadastre o colaborador e defina o alcance das informações.",
        "administracao:usuarios",
    )


@admin_required
def usuario_editar(request: HttpRequest, pk: int) -> HttpResponse:
    usuario = get_object_or_404(Usuario, pk=pk)
    formulario = UsuarioEdicaoForm(request.POST or None, instance=usuario)
    if formulario.is_valid():
        if usuario == request.user and not formulario.cleaned_data.get("is_active"):
            formulario.add_error("is_active", "Você não pode desativar o próprio acesso.")
        else:
            formulario.save()
            messages.success(request, f"Acesso de {usuario.nome_exibicao} atualizado.")
            return redirect("administracao:usuarios")
    return _render_formulario(
        request, formulario, "usuarios", "Editar acesso", usuario.nome_exibicao,
        "administracao:usuarios",
    )


@admin_required
def usuario_alternar(request: HttpRequest, pk: int) -> HttpResponse:
    usuario = get_object_or_404(Usuario, pk=pk)
    if usuario == request.user:
        messages.error(request, "Você não pode desativar o próprio acesso.")
        return redirect("administracao:usuarios")
    if request.method == "POST":
        usuario.is_active = not usuario.is_active
        usuario.save(update_fields=["is_active", "atualizado_em"])
        estado = "reativado" if usuario.is_active else "desativado"
        messages.success(request, f"Acesso de {usuario.nome_exibicao} {estado}.")
        return redirect("administracao:usuarios")
    return render(
        request,
        "accounts/admin/confirmar.html",
        {
            "secao": "usuarios",
            "titulo": "Reativar acesso" if not usuario.is_active else "Desativar acesso",
            "objeto": f"{usuario.nome_exibicao} — {usuario.email}",
            "aviso": (
                "O cadastro será preservado, mas o usuário não conseguirá entrar no SIGA."
                if usuario.is_active else "O usuário voltará a conseguir entrar no SIGA."
            ),
            "voltar": "administracao:usuarios",
            "acao": "Reativar" if not usuario.is_active else "Desativar",
        },
    )


def _render_formulario(request, formulario, secao, titulo, descricao, voltar):
    return render(
        request,
        "accounts/admin/formulario.html",
        {
            "secao": secao, "titulo": titulo, "descricao": descricao,
            "formulario": formulario, "voltar": voltar,
        },
    )
