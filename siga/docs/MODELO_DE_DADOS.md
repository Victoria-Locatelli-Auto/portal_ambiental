# Modelo de dados

```
Unidade (casa)
  └── flags: tem_oficina, tem_poco, opera_em_posto, imovel
       │
       └──► decide quais TipoDocumento são aplicáveis
                    │
TipoDocumento (requisito legal)
  ├── periodicidade_meses  → calcula o vencimento
  ├── dias_alerta          → quando começar a avisar
  ├── aplicabilidade       → TODAS | OFICINA | POCO | POSTO | IMOVEL_TERCEIRO
  ├── responsavel_execucao → CASA | MCM_STX | MCM | STX | STX_ELABORA
  ├── instrucao            → texto lido pela coordenadora
  └── normas ─────────────► NormaLegal (M2M)
       │
Documento (versão enviada)
  ├── unidade + tipo + versao (constraint única)
  ├── versao_corrente      → só uma por (casa, tipo)
  ├── situacao             → fluxo decidido por pessoas
  └── status (property)    → calculado a partir das datas

Condicionante ──► Unidade, evidência opcional ──► Documento

RelatorioAuditoria ──► Unidade
  ├── RespostaCampo ──► PontoVerificacao   (checklist das visitas in loco)
  └── NaoConformidade                       (plano de ação 5W2H)

MovimentacaoResiduo ──► Unidade   (classe NBR 10.004, MTR, CDF)

Notificacao ──► Unidade, Documento   (chave_idempotencia única)
LogAuditoria                          (trilha imutável)
```

## Situação × Status

São coisas diferentes e é proposital:

- **`situacao`** — estado do fluxo de aprovação, decidido por pessoas:
  `RASCUNHO → AGUARDANDO → VALIDADO | REJEITADO`
- **`status`** — estado de conformidade, calculado das datas:
  `PENDENTE | EM_ANALISE | VIGENTE | AVENCER | CRITICO | VENCIDO | NAO_APLICAVEL`

Um documento pode estar `VALIDADO` e mesmo assim `VENCIDO`.

## Índices que importam

| Índice | Consulta que atende |
|---|---|
| `(unidade, tipo, versao_corrente)` | versão vigente — a query mais frequente |
| `(situacao, data_vencimento)` | régua de notificações |
| `(tema, ordem)` | catálogo agrupado por tema legal |
| `chave_idempotencia` único | impede reenvio de notificação |
