"""Painel principal, checklist por casa e relatorio de pendencias."""
from __future__ import annotations

import csv

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render

from apps.compliance.enums import StatusConformidade
from apps.compliance.selectors import (
    checklist_agrupado,
    itens_da_consultoria,
    matriz_conformidade,
    pendencias,
    proximos_vencimentos,
    resumo_da_unidade,
    resumo_geral,
)
from apps.organizacao.selectors import unidades_do_usuario
from apps.dashboard.forms import FiltroPendenciasForm


@login_required
def painel(request: HttpRequest) -> HttpResponse:
    unidades = list(unidades_do_usuario(request.user))
    resumos = resumo_geral(unidades)
    tipos, matriz = matriz_conformidade(unidades)

    total = sum(r.total for r in resumos)
    regulares = sum(r.em_dia + r.a_vencer + r.em_analise * 0.5 for r in resumos)

    return render(
        request,
        "dashboard/painel.html",
        {
            "resumos": resumos,
            "tipos": tipos,
            "matriz": matriz,
            "unidades": unidades,
            "indice_geral": round(regulares / total * 100) if total else 0,
            "total_requisitos": total,
            "total_vencidos": sum(r.vencido for r in resumos),
            "total_criticos": sum(r.critico for r in resumos),
            "total_pendentes": sum(r.pendente for r in resumos),
            "proximos": proximos_vencimentos(unidades),
            "Status": StatusConformidade,
        },
    )


@login_required
def checklist_geral(request: HttpRequest) -> HttpResponse:
    unidades = list(unidades_do_usuario(request.user))
    if len(unidades) == 1:
        return checklist_da_casa(request, unidades[0].codigo)
    return render(
        request,
        "dashboard/checklist_geral.html",
        {"resumos": resumo_geral(unidades), "unidades": unidades},
    )


@login_required
def checklist_da_casa(request: HttpRequest, codigo: str) -> HttpResponse:
    unidade = get_object_or_404(unidades_do_usuario(request.user), codigo=codigo)
    grupos = checklist_agrupado(unidade)

    rotulos = [
        (StatusConformidade.PENDENTE, "Envio pendente", ""),
        (StatusConformidade.VENCIDO, "Vencido", ""),
        (StatusConformidade.CRITICO, "Renovar ja - vence em ate 30 dias", "Prazo curto. Iniciar hoje."),
        (StatusConformidade.AVENCER, "Preparar renovacao - vence em ate 90 dias", "Ja entrou na regua de alertas."),
        (StatusConformidade.EM_ANALISE, "Aguardando validação STX", "Nenhuma acao da casa e necessaria."),
        (StatusConformidade.VIGENTE, "Em dia", ""),
    ]
    return render(
        request,
        "dashboard/checklist_casa.html",
        {
            "unidade": unidade,
            "grupos": [(r[1], r[2], grupos[r[0]], r[0]) for r in rotulos],
            "itens_stx": itens_da_consultoria(unidade),
            "resumo": resumo_da_unidade(unidade),
            "unidades": unidades_do_usuario(request.user),
        },
    )


@login_required
def relatorio_pendencias(request: HttpRequest) -> HttpResponse:
    unidades = list(unidades_do_usuario(request.user))
    itens = pendencias(unidades)
    formulario = FiltroPendenciasForm(request.GET or None, unidades=unidades)
    if formulario.is_valid():
        filtros = formulario.cleaned_data
        if inicio := filtros.get("data_vencimento_de"):
            itens = [item for item in itens if item.vencimento and item.vencimento >= inicio]
        if fim := filtros.get("data_vencimento_ate"):
            itens = [item for item in itens if item.vencimento and item.vencimento <= fim]
        if responsavel := filtros.get("quem_faz"):
            itens = [item for item in itens if responsavel in item.tipo.responsaveis_execucao]
        if casa := filtros.get("casa"):
            itens = [item for item in itens if item.unidade.codigo == casa]
        if situacao := filtros.get("situacao"):
            itens = [item for item in itens if item.status == situacao]
        if cor_agenda := filtros.get("cor_agenda"):
            itens = [item for item in itens if item.tipo.cor_agenda == cor_agenda]

    if request.GET.get("formato") == "csv":
        return _csv_pendencias(itens)
    parametros_exportacao = request.GET.copy()
    parametros_exportacao["formato"] = "csv"
    return render(
        request,
        "dashboard/pendencias.html",
        {
            "itens": itens,
            "unidades": unidades,
            "formulario": formulario,
            "export_query": parametros_exportacao.urlencode(),
        },
    )


def _csv_pendencias(itens) -> HttpResponse:
    resposta = HttpResponse(content_type="text/csv; charset=utf-8-sig")
    resposta["Content-Disposition"] = 'attachment; filename="SIGA_pendencias.csv"'
    escritor = csv.writer(resposta, delimiter=";")
    escritor.writerow(
        ["Situacao", "Casa", "UF", "CNPJ", "Documento", "Tema", "Cor da agenda", "Base legal",
         "Vencimento", "Dias", "Quem faz", "O que fazer", "Responsavel", "E-mail"]
    )
    for i in itens:
        escritor.writerow([
            i.status, i.unidade.nome, i.unidade.uf, i.unidade.cnpj, i.tipo.nome,
            i.tipo.tema_rotulo, i.tipo.get_cor_agenda_display(), i.tipo.base_legal,
            i.vencimento.strftime("%d/%m/%Y") if i.vencimento else "",
            i.dias if i.dias is not None else "",
            i.tipo.get_responsavel_execucao_display(), i.tipo.instrucao,
            i.unidade.responsavel_nome, i.unidade.responsavel_email,
        ])
    return resposta


@login_required
def exportar_checklist(request: HttpRequest, codigo: str) -> HttpResponse:
    unidade = get_object_or_404(unidades_do_usuario(request.user), codigo=codigo)
    from apps.compliance.selectors import checklist_da_unidade

    resposta = HttpResponse(content_type="text/csv; charset=utf-8-sig")
    resposta["Content-Disposition"] = f'attachment; filename="SIGA_checklist_{unidade.codigo}.csv"'
    escritor = csv.writer(resposta, delimiter=";")
    escritor.writerow(
        ["Documento", "Codigo", "Quem faz", "Acao", "O que fazer", "Vencimento",
         "Dias", "Situacao", "Base legal"]
    )
    for i in checklist_da_unidade(unidade):
        escritor.writerow([
            i.tipo.nome, i.tipo.codigo, i.tipo.get_responsavel_execucao_display(), i.verbo,
            i.tipo.instrucao, i.vencimento.strftime("%d/%m/%Y") if i.vencimento else "",
            i.dias if i.dias is not None else "", i.status, i.tipo.base_legal,
        ])
    return resposta
