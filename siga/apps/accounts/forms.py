"""Formulários da área administrativa integrada ao SIGA."""
from __future__ import annotations

from django import forms
from django.contrib.auth import get_user_model
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe

from apps.accounts.models import Perfil
from apps.compliance.enums import Aplicabilidade, ResponsavelExecucao, TemaLegal, valor_unidade
from apps.compliance.models import TemaLegalCadastro, TipoDocumento
from apps.organizacao.models import Unidade

Usuario = get_user_model()


class StyledModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "inp")


class TemaLegalCadastroForm(StyledModelForm):
    class Meta:
        model = TemaLegalCadastro
        fields = ("codigo", "nome", "ordem", "ativo")

    def clean_codigo(self):
        return self.cleaned_data["codigo"].strip().upper().replace(" ", "_")


class CheckboxDropdown(forms.CheckboxSelectMultiple):
    """Multiseleção compacta que abre as opções em uma lista de checkboxes."""

    def format_value(self, value):
        if isinstance(value, str):
            value = [item for item in value.split(",") if item]
        return super().format_value(value)

    def render(self, name, value, attrs=None, renderer=None):
        value = self.format_value(value)
        selecionados = set(value or [])
        opcoes = []
        for codigo, rotulo in self.choices:
            identificador = f"id_{name}_{len(opcoes)}"
            marcado = mark_safe(" checked") if str(codigo) in selecionados else ""
            opcoes.append((identificador, name, codigo, marcado, rotulo))
        itens = format_html_join(
            "", '<label for="{}"><input type="checkbox" id="{}" name="{}" value="{}"{}> <span>{}</span></label>',
            ((i, i, n, c, m, r) for i, n, c, m, r in opcoes),
        )
        resumo = f"{len(selecionados)} selecionado(s)" if selecionados else "Selecione uma ou mais opções"
        return format_html(
            '<details class="checkbox-dropdown">'
            '<summary data-empty="Selecione uma ou mais opções">{}</summary>'
            '<div class="checkbox-dropdown-menu">{}</div></details>',
            resumo, itens,
        )


class TipoDocumentoForm(StyledModelForm):
    aplicabilidade = forms.MultipleChoiceField(
        label="Aplicabilidade",
        choices=(),
        widget=CheckboxDropdown,
    )
    responsavel_execucao = forms.MultipleChoiceField(
        label="Aprovador",
        choices=(),
        widget=CheckboxDropdown,
    )

    class Meta:
        model = TipoDocumento
        fields = (
            "codigo", "nome", "tema", "cor_agenda", "periodicidade_meses", "dias_alerta",
            "quantidade_arquivos", "nome_anexo_complementar",
            "aplicabilidade", "responsavel_execucao", "base_legal", "instrucao",
            "nota_tecnica", "ativo",
        )
        widgets = {
            "cor_agenda": forms.RadioSelect(attrs={"class": "agenda-color-options"}),
            "quantidade_arquivos": forms.RadioSelect(
                attrs={"class": "document-count-options"}
            ),
            "base_legal": forms.Textarea(attrs={"rows": 3}),
            "instrucao": forms.Textarea(attrs={"rows": 3}),
            "nota_tecnica": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["codigo"].label = "Código"
        temas = list(
            TemaLegalCadastro.objects.filter(ativo=True)
            .order_by("ordem", "nome")
            .values_list("codigo", "nome")
        )
        if self.instance and self.instance.pk and self.instance.tema:
            codigos = {codigo for codigo, _ in temas}
            if self.instance.tema not in codigos:
                tema_atual = TemaLegalCadastro.objects.filter(
                    codigo=self.instance.tema
                ).values_list("codigo", "nome").first()
                temas.append(tema_atual or (self.instance.tema, self.instance.tema))
        self.fields["tema"].choices = temas or TemaLegal.choices
        self.fields["periodicidade_meses"].label = "Validade do documento"
        self.fields["quantidade_arquivos"].required = False
        self.fields["dias_alerta"].label = "Antecedência do alerta"
        self.fields["dias_alerta"].help_text = ""
        self.fields["nota_tecnica"].label = "Observação técnica"
        casas = list(
            Unidade.objects.ativos().order_by("nome").values_list("codigo", "nome")
        )
        opcoes_casas = [(valor_unidade(codigo), nome) for codigo, nome in casas]
        opcoes_casas_aplicabilidade = [
            (valor, nome) for valor, nome in opcoes_casas if "posto roma" not in nome.lower()
        ]
        # A aplicabilidade e administrada diretamente por casa. As regras
        # operacionais antigas continuam suportadas no modelo para preservar
        # os cadastros existentes, mas nao devem aparecer em novos formularios.
        self.fields["aplicabilidade"].choices = [
            (Aplicabilidade.TODAS, Aplicabilidade.TODAS.label),
            *opcoes_casas_aplicabilidade,
        ]
        opcoes_casas_aprovador = [
            (valor, nome) for valor, nome in opcoes_casas if "posto roma" not in nome.lower()
        ]
        self.fields["responsavel_execucao"].choices = [
            (ResponsavelExecucao.MCM, ResponsavelExecucao.MCM.label),
            (ResponsavelExecucao.STX, ResponsavelExecucao.STX.label),
            *opcoes_casas_aprovador,
        ]
        if self.instance and self.instance.pk:
            aplicabilidades = self.instance.aplicabilidades
            if Aplicabilidade.TODAS in aplicabilidades:
                aplicabilidades = [
                    Aplicabilidade.TODAS,
                    *(valor for valor, _ in opcoes_casas_aplicabilidade),
                ]
            self.initial["aplicabilidade"] = aplicabilidades
            self.initial["responsavel_execucao"] = self.instance.responsaveis_execucao
        elif not self.is_bound:
            self.initial["aplicabilidade"] = [
                Aplicabilidade.TODAS,
                *(valor for valor, _ in opcoes_casas_aplicabilidade),
            ]

    def clean(self):
        dados = super().clean()
        dados["quantidade_arquivos"] = dados.get("quantidade_arquivos") or 1
        if dados.get("quantidade_arquivos") == 2:
            if not dados.get("nome_anexo_complementar"):
                self.add_error(
                    "nome_anexo_complementar",
                    "Informe o nome do segundo documento.",
                )
        else:
            dados["nome_anexo_complementar"] = ""
        return dados

    def clean_aplicabilidade(self):
        valores = self.cleaned_data["aplicabilidade"]
        if Aplicabilidade.TODAS in valores:
            valores = [
                Aplicabilidade.TODAS,
                *(
                    valor_unidade(codigo)
                    for codigo in Unidade.objects.ativos()
                    .exclude(nome__icontains="Posto Roma")
                    .order_by("nome")
                    .values_list("codigo", flat=True)
                ),
            ]
        return ",".join(dict.fromkeys(valores))

    def clean_responsavel_execucao(self):
        return ",".join(self.cleaned_data["responsavel_execucao"])


class UsuarioFormBase(StyledModelForm):
    class Meta:
        model = Usuario
        fields = (
            "nome_completo", "email", "cargo", "telefone", "perfil", "unidade",
            "recebe_notificacoes", "is_active",
        )

    def clean(self):
        dados = super().clean()
        if dados.get("perfil") == Perfil.UNIDADE and not dados.get("unidade"):
            self.add_error("unidade", "Selecione a unidade do responsável de casa.")
        if dados.get("perfil") != Perfil.UNIDADE:
            dados["unidade"] = None
        return dados


class UsuarioCriacaoForm(UsuarioFormBase):
    senha = forms.CharField(
        label="Senha inicial", min_length=8,
        widget=forms.PasswordInput(attrs={"class": "inp", "autocomplete": "new-password"}),
        help_text="Use pelo menos 8 caracteres.",
    )
    confirmar_senha = forms.CharField(
        label="Confirmar senha",
        widget=forms.PasswordInput(attrs={"class": "inp", "autocomplete": "new-password"}),
    )

    class Meta(UsuarioFormBase.Meta):
        fields = (*UsuarioFormBase.Meta.fields, "senha", "confirmar_senha")

    def clean(self):
        dados = super().clean()
        if dados.get("senha") != dados.get("confirmar_senha"):
            self.add_error("confirmar_senha", "As senhas não coincidem.")
        return dados

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.username = usuario.email
        usuario.set_password(self.cleaned_data["senha"])
        if commit:
            usuario.save()
        return usuario


class UsuarioEdicaoForm(UsuarioFormBase):
    nova_senha = forms.CharField(
        label="Nova senha", required=False, min_length=8,
        widget=forms.PasswordInput(attrs={"class": "inp", "autocomplete": "new-password"}),
        help_text="Deixe em branco para manter a senha atual.",
    )

    class Meta(UsuarioFormBase.Meta):
        fields = (*UsuarioFormBase.Meta.fields, "nova_senha")

    def save(self, commit=True):
        usuario = super().save(commit=False)
        if nova_senha := self.cleaned_data.get("nova_senha"):
            usuario.set_password(nova_senha)
        if commit:
            usuario.save()
        return usuario
