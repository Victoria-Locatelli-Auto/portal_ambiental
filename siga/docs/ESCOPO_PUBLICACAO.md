# Escopo de publicação — SIGA

**Sistema:** SIGA — Sistema Integrado de Gestão Ambiental  
**Organização:** MCM Comércio de Caminhões e Ônibus Ltda.  
**Versão do documento:** 1.0  
**Objetivo:** definir o que será entregue, validado e operado na primeira publicação do SIGA.

## 1. Visão do produto

O SIGA centraliza o controle documental ambiental das casas da MCM. O sistema permite
acompanhar documentos exigidos, responsáveis, aplicabilidade, vencimentos, renovações,
histórico, validações e notificações, mantendo rastreabilidade por casa e por usuário.

### Resultado esperado

- Reduzir documentos vencidos ou nunca enviados.
- Manter um acervo único e rastreável por casa.
- Definir claramente quem executa e quem valida cada obrigação.
- Avisar diariamente sobre documentos próximos do vencimento ou vencidos.
- Oferecer visão consolidada para a gestão e visão restrita para cada casa.

## 2. Público e perfis de acesso

| Perfil | Escopo | Principais permissões |
|---|---|---|
| Administrador | Todas as casas | Configurar tipos, usuários, validar e administrar o sistema |
| Gestor MCM | Todas as casas | Consultar painel, documentos, relatórios e processos |
| STX Engenharia | Todas as casas | Consultar, validar ou rejeitar documentos e acompanhar pendências |
| Responsável de casa | Casa vinculada | Consultar checklist e enviar documentos da própria casa |
| Auditor | Todas as casas | Consulta em modo somente leitura |

O acesso será individual. Contas compartilhadas não fazem parte do processo oficial de
publicação.

## 3. Escopo funcional da primeira publicação

### 3.1 Painel e checklist

- Indicadores consolidados de conformidade, vencidos, próximos do vencimento e nunca enviados.
- Índice de conformidade por casa.
- Matriz casa × requisito legal com legenda e atalhos para envio ou visualização.
- Checklist individual por casa, respeitando a aplicabilidade configurada.

### 3.2 Gestão documental

- Envio de PDF, imagem, laudo ou planilha.
- Data de emissão limitada à data atual.
- Documento com vencimento calculado ou marcado como sem validade.
- Validação e rejeição pela STX ou pelo administrador.
- Histórico permanente de versões, com visualização e download.
- Vários anexos no mesmo envio para tipos do tema **Condicionantes**.

### 3.3 Tipos documentais

- Cadastro, edição, ativação e desativação.
- Tema legal, fundamento, instrução, validade, alerta e cor da agenda.
- Aplicabilidade com múltiplas escolhas.
- Responsáveis pela execução com múltiplas escolhas.
- Aplicação por característica operacional ou por uma ou mais casas específicas.

### 3.4 Processos de Emissão/Renovação

- Processo separado por casa.
- Seleção de documentos já existentes no acervo da casa.
- Controle de início, prazo, protocolo, situação e observações.

### 3.5 Relatórios

- Pendências por criticidade.
- Filtros por período de vencimento, responsável, casa e situação.
- Acesso ao documento relacionado.
- Exportação CSV.

### 3.6 Notificações

- Central de notificações dentro do SIGA.
- E-mail diário para documentos dentro da antecedência configurada.
- E-mail diário para documentos vencidos.
- Escalonamento à diretoria após o prazo definido.
- Cobrança semanal consolidada de documentos nunca enviados.
- Proteção contra envio duplicado do mesmo alerta no mesmo dia.

### 3.7 Administração e auditoria

- Cadastro e edição de usuários e perfis.
- Restrição de dados conforme o perfil e a casa vinculada.
- Registro de envios, validações, rejeições, downloads e notificações.
- Preservação do histórico mesmo após atualização documental.

## 4. Regras essenciais de negócio

1. Um responsável de casa só pode acessar a casa vinculada ao seu usuário.
2. Apenas administrador e STX podem validar ou rejeitar documentos.
3. Auditor não pode alterar dados.
4. A situação de prazo é calculada pelo sistema e não digitada manualmente.
5. Uma nova versão não apaga o arquivo anterior.
6. Um requisito com múltiplas aplicabilidades aparece quando pelo menos uma regra corresponde à casa.
7. Todos os responsáveis selecionados devem aparecer nos relatórios e filtros.
8. Arquivos devem ser acessados apenas por usuários autorizados à respectiva casa.
9. A data de emissão não pode ser futura e o vencimento deve ser posterior à emissão.
10. Alertas por e-mail e no sistema devem compartilhar a mesma origem e manter histórico do disparo.

## 5. Requisitos não funcionais

| Área | Requisito mínimo para publicação |
|---|---|
| Segurança | HTTPS, segredo de produção exclusivo, cookies seguros e acesso por perfil |
| Banco | MySQL de produção separado do ambiente de desenvolvimento |
| Arquivos | Armazenamento persistente, privado e incluído no backup |
| Backup | Banco e anexos diariamente; retenção mínima definida pela MCM |
| Disponibilidade | Serviço iniciado automaticamente e monitorado após reinício do servidor |
| Desempenho | Páginas principais utilizáveis com o volume inicial de casas e documentos |
| Auditoria | Logs de aplicação e trilha de ações preservados e consultáveis |
| Privacidade | Somente dados corporativos necessários; revisão conforme a LGPD |
| Navegadores | Versões corporativas atuais de Chrome e Edge; layout responsivo |
| Horário | `America/Sao_Paulo` em aplicação, tarefas e servidor |

## 6. Arquitetura recomendada para a primeira publicação

- Aplicação Django executada por servidor de aplicação compatível com produção.
- Proxy HTTPS com certificado válido e domínio corporativo.
- MySQL 8 em instância ou serviço gerenciado exclusivo do SIGA.
- Redis para a fila de tarefas.
- Um processo de tarefas e um agendador para as notificações.
- Diretório ou serviço de objetos persistente para os anexos.
- Rotina externa de backup e monitoramento.

O servidor de desenvolvimento (`manage.py runserver`) não será usado em produção.

## 7. Itens obrigatórios antes da publicação

### Diagnóstico atual (31/08/2026)

- **Aplicação:** suíte automatizada aprovada com 105 testes.
- **Banco local:** MySQL em uso no ambiente de desenvolvimento; produção ainda deve ser isolada.
- **E-mail:** backend de console e senha SMTP não configurada; ainda não entrega e-mail real.
- **Segurança:** a checagem de implantação alerta que a chave secreta atual não é adequada.
- **Execução:** servidor de desenvolvimento local; infraestrutura de produção ainda não definida.
- **Anexos:** armazenados no disco local; persistência e backup de produção ainda não definidos.

### P0 — bloqueiam a entrada em produção

- [ ] Definir servidor, provedor ou infraestrutura corporativa.
- [ ] Definir domínio, por exemplo `siga.mcm.com.br`, e emitir certificado HTTPS.
- [ ] Criar banco MySQL exclusivo de produção e usuário com acesso restrito.
- [ ] Gerar `SECRET_KEY` exclusiva e manter segredos fora do repositório.
- [ ] Configurar `ALLOWED_HOSTS` e origem CSRF do domínio definitivo.
- [ ] Definir armazenamento persistente e privado dos anexos.
- [ ] Configurar SMTP corporativo e realizar envio real de teste.
- [ ] Configurar Redis, trabalhador e agendador das notificações.
- [ ] Automatizar backup e testar uma restauração completa.
- [ ] Executar migrações e coleta de arquivos estáticos no ambiente final.
- [ ] Remover ou trocar todas as credenciais de demonstração.
- [ ] Cadastrar usuários reais, perfis e responsáveis de cada casa.
- [ ] Revisar os tipos documentais e dados iniciais com a área ambiental/STX.
- [ ] Executar teste de homologação e obter aceite dos responsáveis.

### P1 — recomendados para o primeiro mês

- [ ] Monitorar disponibilidade, erros, espaço em disco e falhas de e-mail.
- [ ] Definir política formal de retenção e descarte dos arquivos.
- [ ] Criar procedimento de suporte e responsável por incidentes.
- [ ] Realizar treinamento curto por perfil.
- [ ] Revisar permissões e usuários após 30 dias.

## 8. Critérios de aceite para publicação

A publicação será considerada aprovada quando:

1. Todos os testes automatizados passarem no código que será publicado.
2. A verificação de implantação do Django não apresentar bloqueios críticos.
3. Login, logout e restrição por perfil forem homologados.
4. Um responsável conseguir enviar documento e consultar seu histórico.
5. STX conseguir validar e rejeitar um documento.
6. Um tipo com múltiplas casas e executores aparecer corretamente nos checklists e relatórios.
7. Um tipo Condicionantes aceitar vários anexos e preservar todos no histórico.
8. Um e-mail real chegar ao destinatário de teste e a notificação aparecer no SIGA.
9. Download e visualização respeitarem o escopo da casa.
10. Backup e restauração de banco e arquivo forem comprovados.
11. O sistema funcionar em HTTPS no domínio definitivo.
12. O responsável de negócio registrar o aceite da homologação.

## 9. Fora do escopo da primeira publicação

- Aplicativo móvel nativo.
- Assinatura digital ou certificado ICP-Brasil.
- Integração automática com SINIR, MTR, IBAMA ou órgãos estaduais.
- SSO corporativo, salvo se definido como requisito antes da implantação.
- OCR, leitura automática ou classificação de documentos por inteligência artificial.
- Portal externo para fornecedores sem conta corporativa.

Esses itens poderão formar uma segunda fase após a estabilização do uso real.

## 10. Papéis na implantação

| Papel | Responsabilidade |
|---|---|
| Patrocinador MCM | Aprovar escopo, prioridade e entrada em produção |
| Área ambiental MCM | Validar casas, documentos, responsáveis e regras |
| STX | Homologar conteúdo técnico, validação e alertas |
| TI MCM | Infraestrutura, domínio, SMTP, usuários, backup e suporte |
| Desenvolvimento | Preparar versão, migrações, testes, implantação e correções |

## 11. Plano resumido de publicação

1. **Preparação:** fechar infraestrutura, domínio, responsáveis e dados.
2. **Homologação:** publicar em ambiente restrito, importar dados e executar os critérios de aceite.
3. **Produção:** backup inicial, implantação, migrações, estáticos e testes de fumaça.
4. **Entrada em operação:** liberar usuários, ativar notificações e acompanhar diariamente.
5. **Estabilização:** revisar erros, permissões, e-mails e capacidade durante os primeiros 30 dias.

## 12. Decisões que precisam da MCM

- Endereço definitivo do SIGA.
- Onde o sistema será hospedado e quem administrará o servidor.
- Conta remetente e credenciais SMTP.
- Política de backup e prazo de retenção dos documentos.
- Lista oficial de usuários e perfis.
- Responsável de negócio pelo aceite.
- Data de homologação e data desejada para entrada em produção.
