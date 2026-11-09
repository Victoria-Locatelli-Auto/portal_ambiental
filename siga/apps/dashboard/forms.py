"""Filtros das telas gerenciais do dashboard."""
from django import forms

from apps.compliance.enums import ResponsavelExecucao, StatusConformidade, valor_unidade
from apps.compliance.models import CorAgenda


class FiltroPendenciasForm(forms.Form):
    data_vencimento_de = forms.DateField(
        label="Vencimento de",
        required=False,
        widget=forms.DateInput(attrs={"class": "inp", "type": "date"}),
    )
    data_vencimento_ate = forms.DateField(
        label="Vencimento até",
        required=False,
        widget=forms.DateInput(attrs={"class": "inp", "type": "date"}),
    )
    quem_faz = forms.ChoiceField(
        label="Quem faz",
        required=False,
        choices=[("", "Todos"), *ResponsavelExecucao.choices],
        widget=forms.Select(attrs={"class": "inp"}),
    )
    casa = forms.ChoiceField(
        label="Casa",
        required=False,
        widget=forms.Select(attrs={"class": "inp"}),
    )
    situacao = forms.ChoiceField(
        label="Situação",
        required=False,
        choices=[
            ("", "Todas"),
            (StatusConformidade.PENDENTE, StatusConformidade.PENDENTE.label),
            (StatusConformidade.VENCIDO, StatusConformidade.VENCIDO.label),
            (StatusConformidade.CRITICO, StatusConformidade.CRITICO.label),
            (StatusConformidade.AVENCER, StatusConformidade.AVENCER.label),
            (StatusConformidade.EM_ANALISE, StatusConformidade.EM_ANALISE.label),
        ],
        widget=forms.Select(attrs={"class": "inp"}),
    )
    cor_agenda = forms.ChoiceField(
        label="Cor da agenda",
        required=False,
        choices=[("", "Todas"), *CorAgenda.choices],
        widget=forms.Select(attrs={"class": "inp"}),
    )

    def __init__(self, *args, unidades=None, **kwargs):
        super().__init__(*args, **kwargs)
        unidades = list(unidades or [])
        opcoes_unidades = [
            (valor_unidade(unidade.codigo), unidade.nome) for unidade in unidades
        ]
        self.fields["quem_faz"].choices = [
            ("", "Todos"),
            *ResponsavelExecucao.choices,
            *opcoes_unidades,
        ]
        self.fields["casa"].choices = [
            ("", "Todas"),
            *((unidade.codigo, unidade.nome) for unidade in unidades),
        ]

    def clean(self):
        dados = super().clean()
        inicio = dados.get("data_vencimento_de")
        fim = dados.get("data_vencimento_ate")
        if inicio and fim and fim < inicio:
            self.add_error(
                "data_vencimento_ate", "A data final deve ser igual ou posterior à data inicial."
            )
        return dados
