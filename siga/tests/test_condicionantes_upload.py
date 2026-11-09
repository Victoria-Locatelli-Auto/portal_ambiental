from django.core.files.uploadedfile import SimpleUploadedFile

from apps.compliance.enums import TemaLegal
from apps.compliance.forms import EnvioDocumentoForm
from apps.compliance.models import Documento
from apps.compliance.services import enviar_documentos


def test_condicionantes_permite_selecionar_varios_arquivos(tipo_licenca):
    tipo_licenca.tema = TemaLegal.CONDICIONANTES
    formulario = EnvioDocumentoForm(tipo=tipo_licenca)
    assert formulario.fields["arquivo"].widget.allow_multiple_selected
    assert "vários arquivos" in formulario.fields["arquivo"].help_text


def test_outros_temas_continuam_com_apenas_um_arquivo(tipo_licenca):
    formulario = EnvioDocumentoForm(tipo=tipo_licenca)
    assert not formulario.fields["arquivo"].widget.allow_multiple_selected


def test_lote_de_condicionantes_preserva_todos_os_arquivos(
    db, casa, coordenadora, tipo_licenca
):
    tipo_licenca.tema = TemaLegal.CONDICIONANTES
    tipo_licenca.save(update_fields=["tema"])
    arquivos = [
        SimpleUploadedFile("regra-1.pdf", b"arquivo 1", content_type="application/pdf"),
        SimpleUploadedFile("regra-2.pdf", b"arquivo 2", content_type="application/pdf"),
    ]
    criados = enviar_documentos(
        unidade=casa,
        tipo=tipo_licenca,
        usuario=coordenadora,
        identificacao="Condicionantes da licença",
        data_emissao=__import__("datetime").date.today(),
        sem_data_validade=True,
        arquivos=arquivos,
    )
    assert len(criados) == 2
    assert Documento.objects.filter(unidade=casa, tipo=tipo_licenca).count() == 2
    assert {d.versao for d in criados} == {1, 2}
    assert all(d.arquivo for d in criados)
