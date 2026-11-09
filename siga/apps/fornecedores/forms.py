from django import forms

from apps.accounts.forms import CheckboxDropdown
from apps.fornecedores.models import Contrato, Fornecedor
from apps.organizacao.models import Unidade


class StyledModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
            campo.widget.attrs.setdefault("class", "inp")


class FornecedorForm(StyledModelForm):
    class Meta:
        model = Fornecedor
        fields = (
            "razao_social", "nome_fantasia", "cnpj_cpf", "servico_fornecido",
            "responsavel", "email", "telefone", "endereco", "observacoes",
            "cidades_atendidas", "anexo_contrato", "ativo",
        )
        widgets = {
            "observacoes": forms.Textarea(attrs={"rows": 4}),
            "cidades_atendidas": CheckboxDropdown(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        campo = self.fields["cidades_atendidas"]
        campo.label = "Cidades atendidas"
        campo.help_text = "Selecione uma ou mais cidades atendidas pelo fornecedor."
        campo.queryset = Unidade.objects.ativos().exclude(
            nome__icontains="Posto Roma"
        ).order_by("municipio", "nome")
        campo.label_from_instance = lambda unidade: (
            f"{unidade.municipio}/{unidade.uf} — {unidade.nome}"
        )


class ContratoForm(StyledModelForm):
    class Meta:
        model = Contrato
        fields = (
            "numero", "objeto", "data_inicio", "data_fim", "valor", "situacao",
            "arquivo", "observacoes",
        )
        widgets = {
            "objeto": forms.Textarea(attrs={"rows": 4}),
            "data_inicio": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "data_fim": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "valor": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "observacoes": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["arquivo"].label = "Anexo do contrato"
        self.fields["arquivo"].help_text = (
            "Anexe o contrato assinado em PDF, DOC, DOCX ou ODT."
        )

    def clean(self):
        dados = super().clean()
        inicio, fim = dados.get("data_inicio"), dados.get("data_fim")
        if inicio and fim and fim < inicio:
            self.add_error("data_fim", "O fim da vigência não pode ser anterior ao início.")
        return dados

