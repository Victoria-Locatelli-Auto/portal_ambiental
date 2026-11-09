"""Formularios de envio e validacao de documentos."""
from __future__ import annotations

from django import forms
from django.utils import timezone

from apps.compliance.enums import TemaLegal
from apps.compliance.models import (
    Documento,
    ProcessoRenovacao,
    TemaLegalCadastro,
    TipoDocumento,
)
from apps.fornecedores.models import Fornecedor


class DataInput(forms.DateInput):
    input_type = "date"


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def clean(self, data, initial=None):
        limpar = super().clean
        if isinstance(data, (list, tuple)):
            return [limpar(arquivo, initial) for arquivo in data]
        arquivo = limpar(data, initial)
        return [arquivo] if arquivo else []


class EnvioDocumentoForm(forms.Form):
    """Envio de um documento a partir de uma linha do checklist.

    A casa e o tipo vem da URL, nao do formulario: evita que um usuario
    envie documento para outra casa manipulando o POST.
    """

    identificacao = forms.CharField(
        label="Identificacao do documento",
        max_length=255,
        required=False,
        widget=forms.TextInput(
            attrs={"placeholder": "ex.: LO n 1187/2022 - SEMA-MA", "class": "inp"}
        ),
    )
    numero_protocolo = forms.CharField(
        label="Numero do protocolo",
        max_length=120,
        required=False,
        widget=forms.TextInput(
            attrs={"placeholder": "Informe o número do protocolo", "class": "inp"}
        ),
    )
    fornecedor = forms.ModelChoiceField(
        label="Fornecedor",
        queryset=Fornecedor.objects.none(),
        required=False,
        empty_label="Selecione um fornecedor",
        widget=forms.Select(attrs={"class": "inp"}),
        help_text="Selecione o fornecedor relacionado a este documento, quando aplicável.",
    )
    data_emissao = forms.DateField(
        label="Data de emissao", widget=DataInput(attrs={"class": "inp"})
    )
    data_vencimento = forms.DateField(
        label="Data de vencimento",
        required=False,
        widget=DataInput(attrs={"class": "inp"}),
        help_text="Calculada automaticamente pela validade do tipo. Ajuste se necessario.",
    )
    sem_data_validade = forms.BooleanField(
        label="Sem data de validade",
        required=False,
        help_text="Marque quando o documento não possuir vencimento.",
    )
    arquivo = MultipleFileField(
        label="Arquivo (PDF, foto, laudo ou planilha)",
        required=True,
        widget=MultipleFileInput(attrs={"class": "inp"}),
    )
    anexo_complementar = forms.FileField(
        label="Segundo documento",
        required=False,
        widget=forms.ClearableFileInput(attrs={"class": "inp"}),
    )
    observacao = forms.CharField(
        label="Observacao para a STX",
        required=False,
        widget=forms.Textarea(attrs={"rows": 2, "class": "inp"}),
    )

    def __init__(self, *args, tipo: TipoDocumento | None = None, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.tipo = tipo
        self.fields["fornecedor"].queryset = Fornecedor.objects.filter(
            ativo=True
        ).order_by("razao_social")
        if tipo and (tipo.tema != TemaLegal.CONDICIONANTES or tipo.quantidade_arquivos == 2):
            self.fields["arquivo"].widget.allow_multiple_selected = False
            self.fields["arquivo"].widget.attrs.pop("multiple", None)
            self.fields["arquivo"].help_text = "Selecione um arquivo."
        else:
            self.fields["arquivo"].help_text = (
                "Você pode selecionar vários arquivos de uma só vez."
            )
        if tipo and tipo.quantidade_arquivos == 2:
            self.fields["anexo_complementar"].label = tipo.nome_anexo_complementar
            self.fields["anexo_complementar"].required = True
            self.fields["anexo_complementar"].help_text = (
                f"Anexe o documento relacionado: {tipo.nome_anexo_complementar}."
            )
        else:
            self.fields.pop("anexo_complementar")
        self.fields["data_emissao"].widget.attrs["max"] = timezone.localdate().isoformat()
        if tipo and not self.is_bound:
            from apps.core.utils import hoje

            self.fields["data_emissao"].initial = hoje()
            if not tipo.por_evento:
                self.fields["data_vencimento"].initial = tipo.calcular_vencimento(hoje())
            else:
                self.fields["sem_data_validade"].initial = True
            self.fields["identificacao"].widget.attrs["placeholder"] = tipo.nome

    def clean(self):
        dados = super().clean()
        if dados.get("sem_data_validade"):
            dados["data_vencimento"] = None

        emissao, vencimento = dados.get("data_emissao"), dados.get("data_vencimento")
        if emissao and emissao > timezone.localdate():
            self.add_error("data_emissao", "A data de emissão não pode ser posterior à data atual.")
        if emissao and vencimento and vencimento <= emissao:
            self.add_error("data_vencimento", "O vencimento deve ser posterior a emissao.")
        return dados


class RejeicaoForm(forms.Form):
    motivo = forms.CharField(
        label="Motivo da rejeicao",
        widget=forms.Textarea(attrs={"rows": 3, "class": "inp"}),
        help_text="Explique o que a casa precisa corrigir.",
    )


class FiltroDocumentoForm(forms.Form):
    unidade = forms.ChoiceField(
        label="Casa", required=False, widget=forms.Select(attrs={"class": "inp"})
    )
    tema = forms.ChoiceField(
        label="Tema legal", required=False, widget=forms.Select(attrs={"class": "inp"})
    )
    busca = forms.CharField(
        label="Buscar",
        required=False,
        widget=forms.TextInput(
            attrs={"class": "inp", "placeholder": "Documento ou tipo documental"}
        ),
    )

    def __init__(self, *args, unidades=None, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fields["unidade"].choices = [("", "Todas")] + [
            (u.codigo, u.nome) for u in (unidades or [])
        ]
        temas = TemaLegalCadastro.objects.filter(ativo=True).values_list("codigo", "nome")
        self.fields["tema"].choices = [("", "Todos"), *(temas or TemaLegal.choices)]


class DocumentoAdminForm(forms.ModelForm):
    class Meta:
        model = Documento
        fields = "__all__"  # noqa: DJ007

    def clean_data_emissao(self):
        data_emissao = self.cleaned_data["data_emissao"]
        if data_emissao > timezone.localdate():
            raise forms.ValidationError("A data de emissão não pode ser posterior à data atual.")
        return data_emissao


class DocumentoRenovacaoChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, documento):
        return (
            f"{documento.tipo.codigo} · {documento.identificacao} · "
            f"emissão {documento.data_emissao:%d/%m/%Y} · versão {documento.versao}"
        )


class ProcessoRenovacaoForm(forms.ModelForm):
    documentos = DocumentoRenovacaoChoiceField(
        label="Documentos já anexados nesta casa",
        queryset=Documento.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={"class": "renewal-doc-options"}),
        help_text="Selecione os arquivos do acervo que farão parte deste processo.",
    )
    anexos_externos = MultipleFileField(
        label="Novos anexos externos",
        required=False,
        widget=MultipleFileInput(attrs={"class": "inp"}),
        help_text="Selecione um ou mais arquivos do seu computador.",
    )

    class Meta:
        model = ProcessoRenovacao
        fields = (
            "tipo", "situacao", "data_inicio", "prazo", "numero_protocolo",
            "documentos", "anexos_externos", "observacao",
        )
        widgets = {
            "tipo": forms.Select(attrs={"class": "inp"}),
            "situacao": forms.Select(attrs={"class": "inp"}),
            "data_inicio": DataInput(attrs={"class": "inp"}),
            "prazo": DataInput(attrs={"class": "inp"}),
            "numero_protocolo": forms.TextInput(
                attrs={"class": "inp", "placeholder": "Informe após o protocolo"}
            ),
            "observacao": forms.Textarea(attrs={"class": "inp", "rows": 4}),
        }

    def __init__(self, *args, unidade, **kwargs):
        super().__init__(*args, **kwargs)
        self.unidade = unidade
        self.fields["tipo"].queryset = TipoDocumento.objects.aplicaveis_a(unidade)
        self.fields["documentos"].queryset = (
            Documento.objects.ativos()
            .filter(unidade=unidade)
            .select_related("tipo")
            .order_by("tipo__ordem", "tipo__nome", "-data_emissao", "-versao")
        )

    def clean_documentos(self):
        documentos = self.cleaned_data["documentos"]
        if documentos.exclude(unidade=self.unidade).exists():
            raise forms.ValidationError("Selecione apenas documentos da casa deste processo.")
        return documentos
