const fs = require("fs");
const {
  AlignmentType, BorderStyle, Document, Footer, Header, HeadingLevel, ImageRun,
  LevelFormat, PageBreak, PageNumber, Packer, Paragraph, ShadingType, Table,
  TableCell, TableOfContents, TableRow, TextRun, WidthType,
} = require("docx");

const GREEN = "006B47";
const DARK = "123C2E";
const LIGHT = "E8F4EE";
const PALE = "F5FAF7";
const GRAY = "66756F";
const RED = "B4233A";
const CONTENT = 9026;
const output = "docs/ESCOPO_PUBLICACAO_SIGA.docx";

const line = { style: BorderStyle.SINGLE, size: 1, color: "C9DAD2" };
const borders = { top: line, bottom: line, left: line, right: line };

function p(text, options = {}) {
  return new Paragraph({
    spacing: { after: options.after ?? 120, line: 300 },
    alignment: options.alignment,
    keepNext: options.keepNext,
    children: [new TextRun({
      text, bold: options.bold, color: options.color, size: options.size,
      italics: options.italics,
    })],
  });
}

function heading(text, level = 1) {
  return new Paragraph({
    heading: level === 1 ? HeadingLevel.HEADING_1 : HeadingLevel.HEADING_2,
    children: [new TextRun(text)],
  });
}

function bullet(text, reference = "bullets") {
  return new Paragraph({
    numbering: { reference, level: 0 }, spacing: { after: 70, line: 280 },
    children: [new TextRun(text)],
  });
}

function numbered(text) {
  return new Paragraph({
    numbering: { reference: "numbers", level: 0 }, spacing: { after: 80, line: 280 },
    children: [new TextRun(text)],
  });
}

function checkbox(text) {
  return new Paragraph({
    spacing: { after: 80 },
    children: [
      new TextRun({ text: "☐  ", font: "Arial", color: GREEN, bold: true }),
      new TextRun(text),
    ],
  });
}

function table(headers, rows, widths) {
  const cell = (text, width, header = false) => new TableCell({
    width: { size: width, type: WidthType.DXA }, borders,
    shading: { fill: header ? GREEN : "FFFFFF", type: ShadingType.CLEAR },
    margins: { top: 100, bottom: 100, left: 130, right: 130 },
    verticalAlign: "center",
    children: [new Paragraph({
      spacing: { after: 0 },
      children: [new TextRun({ text: String(text), bold: header, color: header ? "FFFFFF" : DARK, size: 19 })],
    })],
  });
  return new Table({
    width: { size: CONTENT, type: WidthType.DXA }, columnWidths: widths,
    rows: [
      new TableRow({ tableHeader: true, children: headers.map((h, i) => cell(h, widths[i], true)) }),
      ...rows.map((row) => new TableRow({ children: row.map((v, i) => cell(v, widths[i])) })),
    ],
  });
}

const logoPath = "static/img/mcm-logo.png";
const logo = fs.existsSync(logoPath)
  ? new ImageRun({
      type: "png", data: fs.readFileSync(logoPath), transformation: { width: 220, height: 72 },
      altText: { title: "MCM", description: "Logomarca da MCM", name: "MCM" },
    })
  : new TextRun({ text: "MCM", bold: true, size: 34, color: GREEN });

const children = [
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 700, after: 900 }, children: [logo] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 160 }, children: [
    new TextRun({ text: "SIGA", bold: true, size: 58, color: GREEN, font: "Arial" }),
  ]}),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 500 }, children: [
    new TextRun({ text: "Sistema Integrado de Gestão Ambiental", size: 28, color: DARK }),
  ]}),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 500, after: 180 }, children: [
    new TextRun({ text: "ESCOPO DE PUBLICAÇÃO", bold: true, size: 38, color: DARK }),
  ]}),
  p("MCM Comércio de Caminhões e Ônibus Ltda.", { alignment: AlignmentType.CENTER, size: 24, color: GRAY }),
  p("Versão 1.0 · 31 de agosto de 2026", { alignment: AlignmentType.CENTER, size: 20, color: GRAY, after: 900 }),
  p("Documento para homologação e entrada em produção", { alignment: AlignmentType.CENTER, italics: true, color: GREEN }),
  new Paragraph({ children: [new PageBreak()] }),

  heading("Sumário"),
  new TableOfContents("", { hyperlink: true, headingStyleRange: "1-2" }),
  new Paragraph({ children: [new PageBreak()] }),

  heading("1. Visão do produto"),
  p("O SIGA centraliza o controle documental ambiental das casas da MCM. O sistema acompanha documentos exigidos, responsáveis, aplicabilidade, vencimentos, renovações, histórico, validações e notificações, mantendo rastreabilidade por casa e por usuário."),
  heading("Resultado esperado", 2),
  ...[
    "Reduzir documentos vencidos ou nunca enviados.",
    "Manter um acervo único, seguro e rastreável por casa.",
    "Definir claramente quem executa e quem valida cada obrigação.",
    "Avisar diariamente sobre documentos próximos do vencimento ou vencidos.",
    "Oferecer visão consolidada à gestão e visão restrita para cada casa.",
  ].map(bullet),

  heading("2. Público e perfis de acesso"),
  table(
    ["Perfil", "Escopo", "Principais permissões"],
    [
      ["Administrador", "Todas as casas", "Configurar tipos e usuários, administrar e validar"],
      ["Gestor MCM", "Todas as casas", "Consultar painel, documentos, relatórios e processos"],
      ["STX Engenharia", "Todas as casas", "Validar ou rejeitar documentos e acompanhar pendências"],
      ["Responsável de casa", "Casa vinculada", "Consultar checklist e enviar documentos da própria casa"],
      ["Auditor", "Todas as casas", "Consulta em modo somente leitura"],
    ],
    [2100, 1900, 5026],
  ),
  p("O acesso será individual. Contas compartilhadas não fazem parte do processo oficial de publicação.", { italics: true, color: GRAY, after: 200 }),

  heading("3. Escopo funcional da primeira publicação"),
  heading("3.1 Painel e checklist", 2),
  ...[
    "Indicadores consolidados de conformidade, vencidos, próximos do vencimento e nunca enviados.",
    "Índice de conformidade por casa.",
    "Matriz casa × requisito legal com legenda e atalhos para envio ou visualização.",
    "Checklist individual por casa, respeitando a aplicabilidade configurada.",
  ].map(bullet),
  heading("3.2 Gestão documental", 2),
  ...[
    "Envio de PDF, imagem, laudo ou planilha.",
    "Data de emissão limitada à data atual e vencimento calculado ou sem validade.",
    "Validação e rejeição pela STX ou pelo administrador.",
    "Histórico permanente de versões, com visualização e download.",
    "Vários anexos no mesmo envio para tipos do tema Condicionantes.",
  ].map(bullet),
  heading("3.3 Tipos documentais", 2),
  ...[
    "Cadastro, edição, ativação e desativação.",
    "Tema legal, fundamento, instrução, validade, alerta e cor da agenda.",
    "Aplicabilidade e responsáveis pela execução com múltiplas escolhas.",
    "Aplicação por característica operacional ou por casas específicas.",
  ].map(bullet),
  heading("3.4 Processos de Emissão/Renovação", 2),
  ...[
    "Processo separado por casa e seleção de documentos já existentes no acervo.",
    "Controle de início, prazo, protocolo, situação e observações.",
  ].map(bullet),
  heading("3.5 Relatórios", 2),
  ...[
    "Pendências ordenadas por criticidade.",
    "Filtros por período de vencimento, responsável, casa e situação.",
    "Acesso ao documento relacionado e exportação CSV.",
  ].map(bullet),
  heading("3.6 Notificações", 2),
  ...[
    "Central de notificações dentro do SIGA.",
    "E-mail diário para documentos próximos do vencimento ou vencidos.",
    "Escalonamento à diretoria e cobrança semanal de documentos nunca enviados.",
    "Proteção contra envio duplicado do mesmo alerta no mesmo dia.",
  ].map(bullet),
  heading("3.7 Administração e auditoria", 2),
  ...[
    "Cadastro e edição de usuários e perfis.",
    "Restrição de dados conforme o perfil e a casa vinculada.",
    "Registro de envios, validações, rejeições, downloads e notificações.",
  ].map(bullet),

  heading("4. Regras essenciais de negócio"),
  ...[
    "Um responsável de casa só pode acessar a casa vinculada ao seu usuário.",
    "Apenas administrador e STX podem validar ou rejeitar documentos.",
    "Auditor não pode alterar dados.",
    "A situação de prazo é calculada pelo sistema e não digitada manualmente.",
    "Uma nova versão não apaga o arquivo anterior.",
    "Múltiplas aplicabilidades funcionam por correspondência inclusiva.",
    "Todos os responsáveis selecionados aparecem nos relatórios e filtros.",
    "Arquivos só podem ser acessados por usuários autorizados à respectiva casa.",
    "A data de emissão não pode ser futura; o vencimento deve ser posterior.",
    "Alertas por e-mail e no sistema compartilham a mesma origem e histórico.",
  ].map(numbered),

  heading("5. Requisitos não funcionais"),
  table(
    ["Área", "Requisito mínimo para publicação"],
    [
      ["Segurança", "HTTPS, segredo exclusivo, cookies seguros e controle por perfil"],
      ["Banco", "MySQL de produção separado do ambiente de desenvolvimento"],
      ["Arquivos", "Armazenamento persistente, privado e incluído no backup"],
      ["Backup", "Banco e anexos diariamente, com retenção definida pela MCM"],
      ["Disponibilidade", "Inicialização automática e monitoramento do serviço"],
      ["Auditoria", "Logs e trilha de ações preservados e consultáveis"],
      ["Privacidade", "Dados corporativos necessários e revisão conforme a LGPD"],
      ["Navegadores", "Chrome e Edge corporativos atuais; layout responsivo"],
    ],
    [2200, 6826],
  ),

  heading("6. Arquitetura recomendada"),
  ...[
    "Aplicação Django executada por servidor de aplicação compatível com produção.",
    "Proxy HTTPS com certificado válido e domínio corporativo.",
    "MySQL 8 exclusivo do SIGA.",
    "Redis, trabalhador e agendador para as notificações.",
    "Armazenamento persistente para anexos, com backup externo.",
    "Monitoramento de disponibilidade, erros, filas e espaço em disco.",
  ].map(bullet),
  p("O servidor de desenvolvimento (manage.py runserver) não será usado em produção.", { bold: true, color: RED }),

  heading("7. Diagnóstico atual"),
  table(
    ["Componente", "Situação em 31/08/2026"],
    [
      ["Aplicação", "Suíte automatizada aprovada com 105 testes"],
      ["Banco local", "MySQL em desenvolvimento; produção ainda deve ser isolada"],
      ["E-mail", "Backend de console e senha SMTP ainda não configurada"],
      ["Segurança", "Chave secreta atual não é adequada à produção"],
      ["Execução", "Servidor local de desenvolvimento; hospedagem não definida"],
      ["Anexos", "Disco local; persistência e backup de produção não definidos"],
    ],
    [2200, 6826],
  ),

  heading("8. Checklist obrigatório antes da publicação"),
  heading("P0 — bloqueiam a entrada em produção", 2),
  ...[
    "Definir servidor, provedor ou infraestrutura corporativa.",
    "Definir domínio e emitir certificado HTTPS.",
    "Criar banco MySQL exclusivo de produção e usuário restrito.",
    "Gerar chave secreta exclusiva e guardar os segredos fora do repositório.",
    "Configurar hosts permitidos e origem CSRF do domínio definitivo.",
    "Definir armazenamento persistente e privado dos anexos.",
    "Configurar SMTP corporativo e realizar envio real de teste.",
    "Configurar Redis, trabalhador e agendador das notificações.",
    "Automatizar backup e testar uma restauração completa.",
    "Executar migrações e coleta dos arquivos estáticos no ambiente final.",
    "Remover ou trocar todas as credenciais de demonstração.",
    "Cadastrar usuários reais, perfis e responsáveis de cada casa.",
    "Revisar tipos documentais e dados iniciais com a área ambiental/STX.",
    "Executar homologação e obter aceite dos responsáveis.",
  ].map(checkbox),
  heading("P1 — recomendados para o primeiro mês", 2),
  ...[
    "Monitorar disponibilidade, erros, espaço em disco e falhas de e-mail.",
    "Definir política formal de retenção e descarte dos arquivos.",
    "Criar procedimento de suporte e responsável por incidentes.",
    "Realizar treinamento curto por perfil.",
    "Revisar permissões e usuários após 30 dias.",
  ].map(checkbox),

  heading("9. Critérios de aceite"),
  ...[
    "Todos os testes automatizados passam no código publicado.",
    "A verificação de implantação não apresenta bloqueios críticos.",
    "Login, logout e restrição por perfil são homologados.",
    "Responsável de casa envia documento e consulta seu histórico.",
    "STX valida e rejeita um documento.",
    "Múltiplas casas e executores aparecem corretamente nos checklists e relatórios.",
    "Condicionantes aceitam vários anexos e preservam todos no histórico.",
    "E-mail real chega ao teste e a notificação aparece no SIGA.",
    "Download e visualização respeitam o escopo da casa.",
    "Backup e restauração do banco e dos arquivos são comprovados.",
    "Sistema funciona em HTTPS no domínio definitivo.",
    "Responsável de negócio registra o aceite da homologação.",
  ].map(numbered),

  heading("10. Fora do escopo da primeira publicação"),
  ...[
    "Aplicativo móvel nativo.",
    "Assinatura digital ou certificado ICP-Brasil.",
    "Integração automática com SINIR, MTR, IBAMA ou órgãos estaduais.",
    "SSO corporativo, salvo se priorizado antes da implantação.",
    "OCR ou classificação automática por inteligência artificial.",
    "Portal externo para fornecedores sem conta corporativa.",
  ].map(bullet),

  heading("11. Papéis na implantação"),
  table(
    ["Papel", "Responsabilidade"],
    [
      ["Patrocinador MCM", "Aprovar escopo, prioridade e entrada em produção"],
      ["Área ambiental MCM", "Validar casas, documentos, responsáveis e regras"],
      ["STX", "Homologar conteúdo técnico, validação e alertas"],
      ["TI MCM", "Infraestrutura, domínio, SMTP, backup e suporte"],
      ["Desenvolvimento", "Versão, migrações, testes, implantação e correções"],
    ],
    [2600, 6426],
  ),

  heading("12. Plano resumido de publicação"),
  ...[
    "Preparação — fechar infraestrutura, domínio, responsáveis e dados.",
    "Homologação — publicar em ambiente restrito, importar dados e executar os critérios.",
    "Produção — realizar backup inicial, implantação, migrações e testes de fumaça.",
    "Entrada em operação — liberar usuários, ativar notificações e acompanhar diariamente.",
    "Estabilização — revisar erros, permissões, e-mails e capacidade por 30 dias.",
  ].map(numbered),

  heading("13. Decisões necessárias da MCM"),
  ...[
    "Endereço definitivo do SIGA.",
    "Local de hospedagem e responsável pelo servidor.",
    "Conta remetente e credenciais SMTP.",
    "Política de backup e retenção dos documentos.",
    "Lista oficial de usuários e perfis.",
    "Responsável de negócio pelo aceite.",
    "Data de homologação e data desejada para produção.",
  ].map(checkbox),

  new Paragraph({ pageBreakBefore: true, alignment: AlignmentType.CENTER, spacing: { before: 1000, after: 400 }, children: [
    new TextRun({ text: "APROVAÇÃO DO ESCOPO", bold: true, size: 32, color: GREEN }),
  ]}),
  p("Este documento registra o escopo previsto para a primeira publicação do SIGA.", { alignment: AlignmentType.CENTER, color: GRAY, after: 900 }),
  table(
    ["Representante", "Nome / assinatura / data"],
    [
      ["Patrocinador MCM", ""],
      ["Área Ambiental MCM", ""],
      ["TI MCM", ""],
      ["STX Engenharia", ""],
    ],
    [3200, 5826],
  ),
];

const doc = new Document({
  creator: "MCM — SIGA",
  title: "Escopo de Publicação — SIGA",
  description: "Escopo funcional e checklist para publicação do SIGA",
  styles: {
    default: { document: { run: { font: "Arial", size: 21, color: DARK } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: "Arial", size: 30, bold: true, color: GREEN },
        paragraph: { spacing: { before: 320, after: 150 }, outlineLevel: 0, keepNext: true,
          border: { bottom: { style: BorderStyle.SINGLE, size: 8, color: GREEN, space: 5 } } } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: "Arial", size: 24, bold: true, color: DARK },
        paragraph: { spacing: { before: 220, after: 100 }, outlineLevel: 1, keepNext: true } },
    ],
  },
  numbering: { config: [
    {
      reference: "bullets",
      levels: [{
        level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 600, hanging: 260 } } },
      }],
    },
    {
      reference: "numbers",
      levels: [{
        level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 620, hanging: 320 } } },
      }],
    },
  ] },
  sections: [{
    properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1150, right: 1440, bottom: 1150, left: 1440 } } },
    headers: { default: new Header({ children: [new Paragraph({
      border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: GREEN, space: 4 } },
      children: [new TextRun({ text: "SIGA  |  ESCOPO DE PUBLICAÇÃO", bold: true, size: 16, color: GREEN })],
    })] }) },
    footers: { default: new Footer({ children: [new Paragraph({
      alignment: AlignmentType.CENTER,
      children: [new TextRun({ text: "MCM Comércio de Caminhões e Ônibus Ltda.   ·   ", size: 16, color: GRAY }),
        new TextRun({ children: [PageNumber.CURRENT], size: 16, color: GRAY })],
    })] }) },
    children,
  }],
});

Packer.toBuffer(doc).then((buffer) => {
  fs.writeFileSync(output, buffer);
  console.log(output);
});
