"""Formulários de configuração da comunicação por e-mail."""
from django import forms
from django.template import Template, TemplateSyntaxError

from apps.notificacoes.models import ModeloEmail


class ModeloEmailForm(forms.ModelForm):
    class Meta:
        model = ModeloEmail
        fields = ("assunto", "corpo", "ativo")
        widgets = {
            "assunto": forms.TextInput(attrs={"class": "inp"}),
            "corpo": forms.Textarea(attrs={"class": "inp", "rows": 18}),
        }

    def _validar_template(self, campo):
        valor = self.cleaned_data[campo]
        try:
            Template(valor)
        except TemplateSyntaxError as erro:
            raise forms.ValidationError(f"Template inválido: {erro}") from erro
        return valor

    def clean_assunto(self):
        assunto = self._validar_template("assunto")
        if "\n" in assunto or "\r" in assunto:
            raise forms.ValidationError("O assunto deve permanecer em uma única linha.")
        return assunto

    def clean_corpo(self):
        return self._validar_template("corpo")


class EmailTesteForm(forms.Form):
    destinatario = forms.EmailField(
        label="E-mail para teste",
        widget=forms.EmailInput(
            attrs={"class": "inp", "placeholder": "nome@mcmtocantins.com"}
        ),
    )
