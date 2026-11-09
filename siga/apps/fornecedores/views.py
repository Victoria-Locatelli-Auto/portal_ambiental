from __future__ import annotations

from django.contrib import messages
from django.db.models import Count, Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.views import admin_required
from apps.fornecedores.forms import ContratoForm, FornecedorForm
from apps.fornecedores.models import Contrato, Fornecedor


@admin_required
def lista(request: HttpRequest) -> HttpResponse:
    busca = request.GET.get("q", "").strip()
    fornecedores = Fornecedor.objects.prefetch_related("cidades_atendidas").annotate(
        total_contratos=Count("contratos")
    )
    if busca:
        fornecedores = fornecedores.filter(
            Q(razao_social__icontains=busca)
            | Q(nome_fantasia__icontains=busca)
            | Q(cnpj_cpf__icontains=busca)
            | Q(servico_fornecido__icontains=busca)
        )
    return render(
        request, "fornecedores/lista.html",
        {"secao": "fornecedores", "fornecedores": fornecedores, "busca": busca},
    )


@admin_required
def criar(request: HttpRequest) -> HttpResponse:
    formulario = FornecedorForm(request.POST or None, request.FILES or None)
    if formulario.is_valid():
        fornecedor = formulario.save()
        messages.success(request, f"Fornecedor {fornecedor} cadastrado com sucesso.")
        return redirect("fornecedores:detalhe", uuid=fornecedor.uuid)
    return _formulario_fornecedor(request, formulario, "Novo fornecedor")


@admin_required
def detalhe(request: HttpRequest, uuid) -> HttpResponse:
    fornecedor = get_object_or_404(Fornecedor, uuid=uuid)
    return render(
        request, "fornecedores/detalhe.html",
        {
            "secao": "fornecedores",
            "fornecedor": fornecedor,
            "contratos": fornecedor.contratos.all(),
        },
    )


@admin_required
def editar(request: HttpRequest, uuid) -> HttpResponse:
    fornecedor = get_object_or_404(Fornecedor, uuid=uuid)
    formulario = FornecedorForm(
        request.POST or None, request.FILES or None, instance=fornecedor
    )
    if formulario.is_valid():
        formulario.save()
        messages.success(request, f"Fornecedor {fornecedor} atualizado.")
        return redirect("fornecedores:detalhe", uuid=fornecedor.uuid)
    return _formulario_fornecedor(request, formulario, f"Editar {fornecedor}", fornecedor)


@admin_required
def alternar(request: HttpRequest, uuid) -> HttpResponse:
    fornecedor = get_object_or_404(Fornecedor, uuid=uuid)
    if request.method == "POST":
        fornecedor.ativo = not fornecedor.ativo
        fornecedor.save(update_fields=["ativo", "atualizado_em"])
        estado = "reativado" if fornecedor.ativo else "desativado"
        messages.success(request, f"Fornecedor {fornecedor} {estado}.")
    return redirect("fornecedores:detalhe", uuid=fornecedor.uuid)


@admin_required
def contrato_criar(request: HttpRequest, uuid) -> HttpResponse:
    fornecedor = get_object_or_404(Fornecedor, uuid=uuid)
    formulario = ContratoForm(request.POST or None, request.FILES or None)
    if formulario.is_valid():
        contrato = formulario.save(commit=False)
        contrato.fornecedor = fornecedor
        contrato.save()
        messages.success(request, f"Contrato {contrato.numero} cadastrado.")
        return redirect("fornecedores:detalhe", uuid=fornecedor.uuid)
    return _formulario_contrato(request, formulario, fornecedor, "Novo contrato")


@admin_required
def contrato_editar(request: HttpRequest, uuid, contrato_uuid) -> HttpResponse:
    fornecedor = get_object_or_404(Fornecedor, uuid=uuid)
    contrato = get_object_or_404(Contrato, uuid=contrato_uuid, fornecedor=fornecedor)
    formulario = ContratoForm(request.POST or None, request.FILES or None, instance=contrato)
    if formulario.is_valid():
        formulario.save()
        messages.success(request, f"Contrato {contrato.numero} atualizado.")
        return redirect("fornecedores:detalhe", uuid=fornecedor.uuid)
    return _formulario_contrato(
        request, formulario, fornecedor, f"Editar contrato {contrato.numero}"
    )


def _formulario_fornecedor(request, formulario, titulo, fornecedor=None):
    return render(
        request, "fornecedores/formulario.html",
        {
            "secao": "fornecedores", "titulo": titulo, "formulario": formulario,
            "fornecedor": fornecedor, "voltar_url": (
                "fornecedores:detalhe" if fornecedor else "fornecedores:lista"
            ),
        },
    )


def _formulario_contrato(request, formulario, fornecedor, titulo):
    return render(
        request, "fornecedores/contrato_formulario.html",
        {
            "secao": "fornecedores", "titulo": titulo,
            "formulario": formulario, "fornecedor": fornecedor,
        },
    )

