# SIGA — Sistema Integrado de Gestão Ambiental
**MCM Comércio de Caminhões e Ônibus Ltda.** · 7 casas · TO / MA / PI
Alinhado à ABNT NBR ISO 14001:2015

Controle de conformidade documental ambiental das unidades da MCM, com checklist por casa,
régua automática de vencimentos por e-mail, não conformidades em 5W2H e trilha de auditoria.

O escopo funcional e o checklist para entrada em produção estão em
[`docs/ESCOPO_PUBLICACAO.md`](docs/ESCOPO_PUBLICACAO.md).

---

## Subir em 4 comandos

```bash
make install     # cria o virtualenv e instala as dependências
make migrate     # cria o banco
make seed        # carrega catálogo legal, 7 casas e os dados das auditorias STX
make run         # http://localhost:8000
```

Sem `make`:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
python manage.py migrate
python manage.py seed_siga
python manage.py runserver
```

**Login de demonstração** — senha `siga2026`:

| E-mail | Perfil | Enxerga |
|---|---|---|
| `tiagoantunesadm@gmail.com` | Administrador | 7 casas + configuração |
| `diretoria@mcm.com.br` | Gestor MCM | 7 casas |
| `stxambiental@gmail.com` | STX Engenharia | 7 casas + validação de documentos |
| `balsas@mcm.com.br` | Responsável de casa | somente Balsas |
| `imperatriz@mcm.com.br` | Responsável de casa | somente Imperatriz |
| `auditoria@mcm.com.br` | Auditor | 7 casas, somente leitura |

---

## Arquitetura

Camadas explícitas. Views e API **não falam com o ORM diretamente**.

```
models.py      estrutura e invariantes de dados
selectors.py   consultas de leitura, sem efeito colateral
services.py    regras de escrita: permissão, versionamento, auditoria
views.py       HTTP: recebe, delega ao service, renderiza
api.py         mesma coisa, em JSON
```

Quem consome o quê:

```
        views ─┐                ┌─ selectors ─┐
               ├─► services ────┤             ├─► models ─► banco
        api ───┘                └─ selectors ─┘
        tasks ─┘
```

```
siga/
├── config/                    settings em camadas, celery, urls, api
│   └── settings/              base · dev · test · prod
├── apps/
│   ├── core/                  models base, trilha de auditoria, utils de calendário
│   ├── accounts/              usuário customizado, perfis e escopo de dados
│   ├── organizacao/           as 7 casas e suas flags operacionais
│   ├── compliance/            catálogo legal, documentos, checklist, condicionantes
│   ├── auditoria/             relatórios de visita, checklist de campo, NC 5W2H
│   ├── residuos/              movimentação com MTR/CDF
│   ├── notificacoes/          régua de e-mails, tasks Celery
│   └── dashboard/             painel, checklist por casa, pendências
├── templates/                 HTML + templates de e-mail
├── tests/                     71 testes
└── docs/
```

---

## Como o sistema decide as coisas

### O checklist não é uma lista fixa
Cada casa tem flags operacionais — `tem_oficina`, `tem_poco`, `opera_em_posto`, `imovel`.
O checklist é **derivado** do cruzamento dessas flags com o campo `aplicabilidade` de cada
requisito legal. Marcar "tem oficina" no admin já faz aparecer SAO, laudo de efluente e
monitoramento de solo naquela casa. Nenhuma lista precisa ser editada à mão.

> Balsas não tem área de mecânica, então os requisitos de caixa separadora água/óleo
> simplesmente não existem para ela — não aparecem como pendência nem derrubam o percentual.

### Status é calculado, nunca digitado
`calcular_status()` em `apps/compliance/models.py` é a fonte única de verdade. O painel, o
checklist, o relatório de pendências e a régua de e-mails chamam a mesma função — por isso
todos mostram o mesmo número.

| Prazo restante | Status |
|---|---|
| sem documento | Não enviado |
| enviado, aguardando STX | Em análise |
| vencido | Vencido |
| ≤ 30 dias | Crítico |
| ≤ 90 dias | A vencer |
| acima disso, ou sem validade | Em dia |

### Régua de notificações
- Alerta **diário** enquanto o documento estiver dentro da antecedência configurada no tipo.
- Documento vencido: aviso **diário**, com escalonamento à diretoria após 15 dias.
- Documentos nunca enviados: **uma única cobrança semanal consolidada por casa**, não um
  e-mail por documento.
- Itens conduzidos pela STX são cobrados da consultoria, não da coordenadora da casa.
- **Idempotência**: `chave_idempotencia` limita cada documento a um alerta por dia.

A antecedência de 120 dias continua disponível para licenças por causa do art. 18, §4º da
Res. CONAMA 237/1997 — só o protocolo feito com essa antecedência prorroga a validade da
licença até a decisão do órgão.

```bash
python manage.py enviar_notificacoes --previa       # simula, não envia nem grava
python manage.py enviar_notificacoes                # dispara
celery -A config worker -l info                     # produção
celery -A config beat -l info                       # agendador
```

### Versionamento documental
Enviar um documento do mesmo tipo cria uma nova versão e arquiva a anterior
(`versao_corrente=False`). O histórico nunca é apagado — exigência de rastreabilidade.
`Documento.objects.vigentes()` sempre traz só a versão corrente.

---

## Testes

```bash
make test                    # pytest com cobertura
pytest tests/test_status.py  # só o motor de status
```

71 testes cobrindo: aritmética de calendário (fim de mês, ano bissexto), faixas de status,
regras de aplicabilidade, versionamento, permissões por perfil, gatilhos da régua,
consolidação e idempotência das notificações, fluxo ponta a ponta pelas telas e o seed.

---

## API REST

```
GET  /api/unidades/
GET  /api/tipos-documento/
GET  /api/documentos/
POST /api/documentos/                          envia (passa pelo service)
POST /api/documentos/{uuid}/validar/
GET  /api/documentos/checklist/{codigo_casa}/  checklist pronto da casa
GET  /api/nao-conformidades/
GET  /api/residuos/
```

Todos os endpoints aplicam o escopo do perfil: a coordenadora de Balsas só recebe Balsas.

---

## Como estender

**Novo requisito legal** → `/admin/` ou a lista `TIPOS_DOCUMENTO` em
`apps/core/fixtures/dados.py`, depois `python manage.py seed_siga`.
Preencha `instrucao` em linguagem direta: é o texto que a coordenadora lê no checklist.

**Nova casa** → `/admin/` ou a lista `CASAS`. Marque as flags operacionais corretamente;
o checklist se monta sozinho.

**Nova regra de aplicabilidade** → adicione em `Aplicabilidade` (`apps/compliance/enums.py`),
trate em `TipoDocumento.aplica_a()` e no queryset `aplicaveis_a()`.

**Mudar a régua** → ajuste `dias_alerta` no cadastro do tipo documental.

**Integrar SMTP real** → só variáveis no `.env`. O código já usa o backend do Django.

---

## Origem dos dados

- Objeto do Contrato Ambiental v2 (MCM × STX Engenharia e Meio Ambiente Ltda.)
- Cronograma_Ambiental_MCM-STX.xlsx
- Relatórios de Auditoria e Monitoramento Interno 001 — STX Engenharia, visitas in loco de
  25 a 27/06/2025 (Balsas, Imperatriz, Galpão Tibiri e Posto Roma), Eng. Ambiental
  Tales Gonçalves Pereira, CREA-TO 307764/D.

Gurupi e Araguaína ainda não têm relatório; o de Teresina consta no acervo apenas como
atalho de link — por isso essas casas aparecem com índice baixo. É informação real, não falha
de carga.

---

## Pendente para produção

| Item | O que falta |
|---|---|
| SMTP | Apontar `.env` para o servidor corporativo |
| Banco | Trocar SQLite por Postgres (`DATABASE_URL`) |
| Arquivos | Definir retenção mínima de 5 anos para os PDFs |
| Autenticação | SSO com o domínio `mcm.com.br` |
| Backup | Rotina diária, retenção de 90 dias |
| SINIR / MTR | Importação automática (a avaliar) |
| CTF/APP IBAMA | Consulta de regularidade (a avaliar) |
