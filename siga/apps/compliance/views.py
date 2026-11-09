"""Telas de conformidade: gestao documental, envio e validacao."""
from __future__ import annotations

import mimetypes
from io import BytesIO
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Q
from django.http import FileResponse, Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.compliance import services
from apps.compliance.forms import (
    EnvioDocumentoForm,
    FiltroDocumentoForm,
    ProcessoRenovacaoForm,
    RejeicaoForm,
)
from apps.compliance.models import (
    AnexoProcessoRenovacao,
    Documento,
    ProcessoRenovacao,
    TipoDocumento,
)
from apps.compliance.selectors import historico_do_documento
from apps.core.models import LogAuditoria
from apps.core.services import registrar
from apps.organizacao.selectors import unidades_do_usuario


@login_required
def lista_documentos(request: HttpRequest) -> HttpResponse:
    unidades = unidades_do_usuario(request.user)
    formulario = FiltroDocumentoForm(request.GET or None, unidades=unidades)

    documentos = (
        Documento.objects.vigentes()
        .filter(unidade__in=unidades)
        .select_related("unidade", "tipo", "enviado_por", "validado_por", "fornecedor")
        .order_by("data_vencimento")
    )
    if formulario.is_valid():
        if codigo := formulario.cleaned_data.get("unidade"):
            documentos = documentos.filter(unidade__codigo=codigo)
        if tema := formulario.cleaned_data.get("tema"):
            documentos = documentos.filter(tipo__tema=tema)
        if busca := formulario.cleaned_data.get("busca"):
            documentos = documentos.filter(
                Q(identificacao__icontains=busca) | Q(tipo__nome__icontains=busca)
            )

    return render(
        request,
        "compliance/documentos.html",
        {"documentos": documentos, "formulario": formulario, "unidades": unidades},
    )


@login_required
def enviar_documento(request: HttpRequest, codigo_casa: str, codigo_tipo: str) -> HttpResponse:
    """Upload de um item especifico do checklist.

    A casa e o tipo vem da URL e sao validados contra o escopo do usuario.
    """
    unidade = get_object_or_404(unidades_do_usuario(request.user), codigo=codigo_casa)
    tipo = get_object_or_404(TipoDocumento.objects.ativos(), codigo=codigo_tipo)
    atual = Documento.objects.vigentes().filter(unidade=unidade, tipo=tipo).first()

    if request.method == "POST":
        formulario = EnvioDocumentoForm(request.POST, request.FILES, tipo=tipo)
        if formulario.is_valid():
            try:
                documentos = services.enviar_documentos(
                    unidade=unidade,
                    tipo=tipo,
                    usuario=request.user,
                    identificacao=formulario.cleaned_data["identificacao"],
                    numero_protocolo=formulario.cleaned_data["numero_protocolo"],
                    data_emissao=formulario.cleaned_data["data_emissao"],
                    data_vencimento=formulario.cleaned_data["data_vencimento"],
                    sem_data_validade=formulario.cleaned_data["sem_data_validade"],
                    fornecedor=formulario.cleaned_data["fornecedor"],
                    arquivos=formulario.cleaned_data["arquivo"],
                    anexo_complementar=formulario.cleaned_data.get("anexo_complementar"),
                    observacao=formulario.cleaned_data["observacao"],
                )
            except (PermissionDenied, ValidationError) as erro:
                messages.error(request, getattr(erro, "message", str(erro)))
            else:
                messages.success(
                    request,
                    f"{len(documentos)} documento(s) incluído(s): {tipo.nome}. "
                    "O item saiu da lista de pendências e "
                    "aguarda validacao da STX Engenharia.",
                )
                return redirect("dashboard:checklist", codigo=unidade.codigo)
    else:
        formulario = EnvioDocumentoForm(tipo=tipo)

    return render(
        request,
        "compliance/enviar_documento.html",
        {"formulario": formulario, "unidade": unidade, "tipo": tipo, "atual": atual},
    )


@login_required
def detalhe_documento(request: HttpRequest, uuid) -> HttpResponse:
    documento = get_object_or_404(
        Documento.objects.select_related("unidade", "tipo", "fornecedor"),
        uuid=uuid,
        unidade__in=unidades_do_usuario(request.user),
    )
    return render(
        request,
        "compliance/detalhe_documento.html",
        {
            "documento": documento,
            "historico": historico_do_documento(documento.unidade, documento.tipo),
            "formulario_rejeicao": RejeicaoForm(),
        },
    )


@login_required
def baixar_documento(request: HttpRequest, uuid) -> FileResponse:
    """Entrega o arquivo somente a usuários com acesso à unidade do documento."""
    documento = get_object_or_404(
        Documento.objects.select_related("unidade", "tipo"),
        uuid=uuid,
        unidade__in=unidades_do_usuario(request.user),
    )
    if not documento.arquivo:
        raise Http404("Esta versão não possui arquivo anexado.")

    try:
        arquivo = documento.arquivo.open("rb")
    except (FileNotFoundError, OSError) as erro:
        raise Http404("O arquivo desta versão não foi encontrado.") from erro

    registrar(
        LogAuditoria.Acao.EXPORTACAO,
        f"Download: {documento.tipo.nome} - {documento.unidade.nome}",
        detalhe=f"versão {documento.versao} | {documento.arquivo.name}",
        usuario=request.user,
        entidade="Documento",
        entidade_id=documento.pk,
    )
    return FileResponse(
        arquivo,
        as_attachment=True,
        filename=Path(documento.arquivo.name).name,
    )


@login_required
def visualizar_documento(request: HttpRequest, uuid) -> FileResponse:
    """Abre o arquivo no navegador sem expor diretamente a pasta de mídia."""
    documento = get_object_or_404(
        Documento.objects.select_related("unidade", "tipo"),
        uuid=uuid,
        unidade__in=unidades_do_usuario(request.user),
    )
    if not documento.arquivo:
        raise Http404("Esta versão não possui arquivo anexado.")
    try:
        arquivo = documento.arquivo.open("rb")
    except (FileNotFoundError, OSError) as erro:
        raise Http404("O arquivo desta versão não foi encontrado.") from erro

    nome = Path(documento.arquivo.name).name
    tipo_conteudo = mimetypes.guess_type(nome)[0] or "application/octet-stream"
    registrar(
        LogAuditoria.Acao.EXPORTACAO,
        f"Visualização: {documento.tipo.nome} - {documento.unidade.nome}",
        detalhe=f"versão {documento.versao} | {documento.arquivo.name}",
        usuario=request.user,
        entidade="Documento",
        entidade_id=documento.pk,
    )
    return FileResponse(
        arquivo,
        as_attachment=False,
        filename=nome,
        content_type=tipo_conteudo,
    )


@login_required
def visualizar_anexo_complementar(request: HttpRequest, uuid) -> FileResponse:
    """Abre o segundo documento relacionado com as mesmas regras de acesso."""
    documento = get_object_or_404(
        Documento.objects.select_related("unidade", "tipo"),
        uuid=uuid,
        unidade__in=unidades_do_usuario(request.user),
    )
    if not documento.anexo_complementar:
        raise Http404("Esta versão não possui segundo documento anexado.")
    try:
        arquivo = documento.anexo_complementar.open("rb")
    except (FileNotFoundError, OSError) as erro:
        raise Http404("O segundo documento desta versão não foi encontrado.") from erro

    nome = Path(documento.anexo_complementar.name).name
    tipo_conteudo = mimetypes.guess_type(nome)[0] or "application/octet-stream"
    registrar(
        LogAuditoria.Acao.EXPORTACAO,
        f"Visualização de anexo: {documento.tipo.nome} - {documento.unidade.nome}",
        detalhe=f"versão {documento.versao} | {documento.anexo_complementar.name}",
        usuario=request.user,
        entidade="Documento",
        entidade_id=documento.pk,
    )
    return FileResponse(
        arquivo,
        as_attachment=False,
        filename=nome,
        content_type=tipo_conteudo,
    )


@login_required
@require_POST
def validar_documento(request: HttpRequest, uuid) -> HttpResponse:
    documento = get_object_or_404(Documento, uuid=uuid)
    try:
        services.validar_documento(documento=documento, usuario=request.user)
    except (PermissionDenied, ValidationError) as erro:
        messages.error(request, getattr(erro, "message", str(erro)))
    else:
        messages.success(request, f"{documento.tipo.nome} validado.")
    return redirect("compliance:detalhe_documento", uuid=documento.uuid)


@login_required
@require_POST
def rejeitar_documento(request: HttpRequest, uuid) -> HttpResponse:
    documento = get_object_or_404(Documento, uuid=uuid)
    formulario = RejeicaoForm(request.POST or None)
    if formulario.is_valid():
        try:
            services.rejeitar_documento(
                documento=documento,
                usuario=request.user,
                motivo=formulario.cleaned_data["motivo"],
            )
        except (PermissionDenied, ValidationError) as erro:
            messages.error(request, getattr(erro, "message", str(erro)))
        else:
            messages.warning(request, "Documento devolvido a casa para correcao.")
    else:
        messages.error(request, "Informe o motivo da recusa do documento.")
    return redirect("compliance:detalhe_documento", uuid=documento.uuid)


@login_required
def lista_renovacoes(request: HttpRequest) -> HttpResponse:
    unidades = list(unidades_do_usuario(request.user))
    processos = list(
        ProcessoRenovacao.objects.filter(unidade__in=unidades)
        .select_related("unidade", "tipo", "criado_por")
        .prefetch_related("documentos", "anexos_externos")
    )
    grupos = [
        (unidade, [processo for processo in processos if processo.unidade_id == unidade.pk])
        for unidade in unidades
    ]
    return render(
        request,
        "compliance/renovacoes.html",
        {"grupos": grupos, "total_processos": len(processos), "secao": "renovacoes"},
    )


@login_required
def criar_renovacao(request: HttpRequest, codigo_casa: str) -> HttpResponse:
    if request.user.somente_leitura:
        raise PermissionDenied("Perfil somente leitura não pode criar processos de renovação.")
    unidade = get_object_or_404(unidades_do_usuario(request.user), codigo=codigo_casa)
    formulario = ProcessoRenovacaoForm(
        request.POST or None, request.FILES or None, unidade=unidade
    )
    if formulario.is_valid():
        processo = formulario.save(commit=False)
        processo.unidade = unidade
        processo.criado_por = request.user
        processo.save()
        formulario.save_m2m()
        for arquivo in formulario.cleaned_data["anexos_externos"]:
            AnexoProcessoRenovacao.objects.create(
                processo=processo, arquivo=arquivo, enviado_por=request.user
            )
        registrar(
            LogAuditoria.Acao.CRIACAO,
            f"Processo de emissão/renovação: {processo.tipo.nome} - {unidade.nome}",
            usuario=request.user,
            entidade="ProcessoRenovacao",
            entidade_id=processo.pk,
        )
        messages.success(request, f"Processo de emissão/renovação criado para {unidade.nome}.")
        return redirect("compliance:renovacoes")
    return render(
        request,
        "compliance/renovacao_form.html",
        {
            "formulario": formulario,
            "unidade": unidade,
            "titulo": "Processo de Emissão/ Renovação",
            "secao": "renovacoes",
        },
    )


@login_required
def editar_renovacao(request: HttpRequest, uuid) -> HttpResponse:
    if request.user.somente_leitura:
        raise PermissionDenied("Perfil somente leitura não pode alterar processos de renovação.")
    processo = get_object_or_404(
        ProcessoRenovacao.objects.select_related("unidade", "tipo"),
        uuid=uuid,
        unidade__in=unidades_do_usuario(request.user),
    )
    formulario = ProcessoRenovacaoForm(
        request.POST or None,
        request.FILES or None,
        instance=processo,
        unidade=processo.unidade,
    )
    if formulario.is_valid():
        processo = formulario.save()
        for arquivo in formulario.cleaned_data["anexos_externos"]:
            AnexoProcessoRenovacao.objects.create(
                processo=processo, arquivo=arquivo, enviado_por=request.user
            )
        registrar(
            LogAuditoria.Acao.ALTERACAO,
            f"Processo de emissão/renovação: {processo.tipo.nome} - {processo.unidade.nome}",
            usuario=request.user,
            entidade="ProcessoRenovacao",
            entidade_id=processo.pk,
        )
        messages.success(request, "Processo de emissão/renovação atualizado.")
        return redirect("compliance:renovacoes")
    return render(
        request,
        "compliance/renovacao_form.html",
        {
            "formulario": formulario,
            "unidade": processo.unidade,
            "processo": processo,
            "titulo": "Processo de Emissão/ Renovação",
            "secao": "renovacoes",
        },
    )


@login_required
@require_POST
def cancelar_renovacao(request: HttpRequest, uuid) -> HttpResponse:
    processo = get_object_or_404(
        ProcessoRenovacao.objects.select_related("unidade", "tipo"),
        uuid=uuid,
        unidade__in=unidades_do_usuario(request.user),
    )
    try:
        services.cancelar_processo_renovacao(
            processo=processo,
            usuario=request.user,
        )
    except (PermissionDenied, ValidationError) as erro:
        messages.error(request, getattr(erro, "message", str(erro)))
    else:
        messages.warning(request, "Processo de emissão/renovação cancelado.")
    return redirect("compliance:renovacoes")


@login_required
def baixar_compilado_renovacao(request: HttpRequest, uuid) -> FileResponse:
    """Reúne documentos selecionados e anexos externos em um único ZIP."""
    processo = get_object_or_404(
        ProcessoRenovacao.objects.select_related("unidade", "tipo").prefetch_related(
            "documentos", "anexos_externos"
        ),
        uuid=uuid,
        unidade__in=unidades_do_usuario(request.user),
    )
    buffer = BytesIO()
    nomes_usados: set[str] = set()
    ausentes: list[str] = []
    total = 0

    def adicionar(campo_arquivo, pasta: str, rotulo: str) -> None:
        nonlocal total
        if not campo_arquivo:
            return
        nome_original = Path(campo_arquivo.name).name
        nome = f"{pasta}/{nome_original}"
        contador = 2
        while nome.casefold() in nomes_usados:
            origem = Path(nome_original)
            nome = f"{pasta}/{origem.stem}-{contador}{origem.suffix}"
            contador += 1
        try:
            with campo_arquivo.open("rb") as origem:
                conteudo = origem.read()
        except (FileNotFoundError, OSError):
            ausentes.append(f"{rotulo}: {nome_original}")
            return
        arquivo_zip.writestr(nome, conteudo)
        nomes_usados.add(nome.casefold())
        total += 1

    with ZipFile(buffer, "w", compression=ZIP_DEFLATED) as arquivo_zip:
        for documento in processo.documentos.all():
            adicionar(
                documento.arquivo,
                "documentos-do-acervo",
                documento.identificacao,
            )
            adicionar(
                documento.anexo_complementar,
                "documentos-do-acervo",
                documento.nome_anexo_complementar or documento.identificacao,
            )
        for anexo in processo.anexos_externos.all():
            adicionar(anexo.arquivo, "anexos-externos", str(anexo))
        if ausentes:
            arquivo_zip.writestr(
                "arquivos-nao-encontrados.txt",
                "Os seguintes arquivos não foram encontrados no armazenamento:\n"
                + "\n".join(ausentes),
            )

    if not total:
        raise Http404("Este processo ainda não possui arquivos disponíveis para baixar.")

    buffer.seek(0)
    nome_zip = f"{processo.unidade.codigo}-{processo.tipo.codigo}-documentos.zip"
    registrar(
        LogAuditoria.Acao.EXPORTACAO,
        f"Compilado da renovação: {processo.tipo.nome} - {processo.unidade.nome}",
        detalhe=f"{total} arquivo(s) incluído(s)",
        usuario=request.user,
        entidade="ProcessoRenovacao",
        entidade_id=processo.pk,
    )
    return FileResponse(
        buffer,
        as_attachment=True,
        filename=nome_zip,
        content_type="application/zip",
    )


@login_required
def baixar_anexo_renovacao(request: HttpRequest, uuid) -> FileResponse:
    """Entrega um anexo externo somente a usuários com acesso à casa do processo."""
    anexo = get_object_or_404(
        AnexoProcessoRenovacao.objects.select_related(
            "processo", "processo__unidade", "processo__tipo"
        ),
        uuid=uuid,
        processo__unidade__in=unidades_do_usuario(request.user),
    )
    try:
        arquivo = anexo.arquivo.open("rb")
    except (FileNotFoundError, OSError) as erro:
        raise Http404("O anexo deste processo não foi encontrado.") from erro

    registrar(
        LogAuditoria.Acao.EXPORTACAO,
        f"Download de anexo da renovação: {anexo.processo.tipo.nome} - "
        f"{anexo.processo.unidade.nome}",
        detalhe=anexo.arquivo.name,
        usuario=request.user,
        entidade="AnexoProcessoRenovacao",
        entidade_id=anexo.pk,
    )
    return FileResponse(
        arquivo,
        as_attachment=True,
        filename=Path(anexo.arquivo.name).name,
    )
