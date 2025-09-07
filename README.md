# 🏛️ Sistema de Controle de Precatórios

Um sistema web desenvolvido em Django para gerenciar precatórios judiciários, clientes, alvarás e requerimentos de forma eficiente e organizada.

![Django](https://img.shields.io/badge/Django-3.1.12-green?style=flat-square&logo=django)
![Python](https://img.shields.io/badge/Python-3.x-blue?style=flat-square&logo=python)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3.0-purple?style=flat-square&logo=bootstrap)
![Multi-Environment](https://img.shields.io/badge/Deployment-Multi--Environment-orange?style=flat-square&logo=docker)
![Local](https://img.shields.io/badge/Local-SQLite-lightblue?style=flat-square&logo=sqlite)
![Production](https://img.shields.io/badge/Production-PostgreSQL+S3-red?style=flat-square&logo=amazon-aws)

## 📋 Índice

- [Sobre o Projeto](#sobre-o-projeto)
- [Funcionalidades](#funcionalidades)
- [Tecnologias Utilizadas](#tecnologias-utilizadas)
- [Instalação](#instalação)
- [Uso](#uso)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Modelos de Dados](#modelos-de-dados)
- [Screenshots](#screenshots)
- [Contribuição](#contribuição)
- [Licença](#licença)

## 🎯 Sobre o Projeto

O Sistema de Controle de Precatórios é uma aplicação web desenvolvida para facilitar o gerenciamento de precatórios judiciários, permitindo o controle completo de clientes, alvarás, requerimentos e toda a documentação associada aos processos.

### Principais Objetivos:
- **Organização**: Centralizar todas as informações de precatórios em um só lugar
- **Eficiência**: Agilizar o processo de cadastro e consulta de dados
- **Controle**: Acompanhar o status e evolução dos processos
- **Relatórios**: Gerar informações consolidadas para tomada de decisão

## ✨ Funcionalidades

### 🏛️ **Gestão de Precatórios**
- ✅ Cadastro completo com CNJ, valores e percentuais
- ✅ Controle de status (quitado, prioridade, acordo)
- ✅ Acompanhamento de atualizações monetárias
- ✅ Visualização detalhada com informações financeiras
- ✅ Edição inline com formulários dinâmicos
- ✅ **Sistema de tipos/categorias** com cores personalizáveis
- ✅ **Classificação por tipos** (Alimentar, Comum, etc.)

### 🎨 **Gestão de Tipos de Precatórios**
- ✅ Criação de tipos personalizados para categorização
- ✅ Sistema de cores para identificação visual
- ✅ Ordenação customizável dos tipos
- ✅ Ativação/desativação de tipos
- ✅ Descrições detalhadas para cada tipo
- ✅ CRUD completo com interface intuitiva

### 👥 **Gestão de Clientes**
- ✅ Cadastro de clientes com CPF, nome e data de nascimento
- ✅ Sistema de prioridade legal
- ✅ Vinculação automática com precatórios
- ✅ CRUD completo (Create, Read, Update, Delete)
- ✅ Proteção contra exclusão de clientes com dados associados

### 📄 **Gestão de Alvarás**
- ✅ Cadastro com valores financeiros detalhados
- ✅ Controle de fases (depósito, recebimento, etc.)
- ✅ Cálculos automáticos de honorários
- ✅ Sistema de edição dropdown integrado
- ✅ Relatórios de valores consolidados

### 📋 **Gestão de Requerimentos**
- ✅ Controle de pedidos e valores
- ✅ Sistema de deságio
- ✅ Acompanhamento de fases processuais
- ✅ Interface de edição avançada
- ✅ Filtros e buscas inteligentes

### ✨ **Funcionalidades Avançadas**
- ✅ Sistema de fases customizáveis (com ordenação)
- ✅ Tipos de diligência configuráveis
- ✅ Honorários contratuais com fases específicas
- ✅ Importação de dados via Excel
- ✅ Comandos de gerenciamento customizados
- ✅ Formatação brasileira de números e datas
- ✅ Validação avançada de CPF/CNPJ e CNJ
- ✅ **Sistema de tipos/categorias de precatórios**
- ✅ **Gestão visual com cores personalizáveis**
- ✅ **Filtros e organizações por tipos**

### 🎨 **Sistema de Tipos e Categorização**
- ✅ Tipos de precatórios totalmente customizáveis
- ✅ Tipos de diligências com gestão completa
- ✅ Identificação visual com cores hexadecimais
- ✅ Sistema de ordenação para organização lógica
- ✅ Ativação/desativação para controle de ciclo de vida
- ✅ Descrições detalhadas para melhor compreensão

### 🔍 **Gestão de Diligências**
- ✅ Sistema completo de diligências
- ✅ Tipos customizáveis com cores
- ✅ Controle de urgência e prazos
- ✅ Acompanhamento de conclusão
- ✅ Interface de atualização em tempo real

### 🔐 **Sistema de Autenticação**
- ✅ Login/logout seguro
- ✅ Proteção de todas as rotas com @login_required
- ✅ Sessões de usuário gerenciadas
- ✅ Interface de login customizada

### 🎨 **Interface de Usuário**
- ✅ Design responsivo com Bootstrap 5.3
- ✅ Ícones Font Awesome para melhor UX
- ✅ Modais de confirmação para ações críticas
- ✅ Formulários com validação em tempo real
- ✅ Navegação breadcrumb intuitiva

## 🛠️ Tecnologias Utilizadas

### **Backend**
- **Django 3.1.12** - Framework web Python
- **SQLite** - Banco de dados (desenvolvimento)
- **Python 3.x** - Linguagem de programação

### **Frontend**
- **Bootstrap 5.3.0** - Framework CSS responsivo
- **Font Awesome** - Biblioteca de ícones
- **JavaScript/jQuery** - Interatividade e AJAX
- **HTML5 & CSS3** - Estrutura e estilização

### **Desenvolvimento**
- **Git** - Controle de versão
- **VS Code** - Editor de código
- **Django Admin** - Interface administrativa
- **Django Forms** - Validação e processamento de formulários

### **Dependências Python**
- **openpyxl** - Manipulação de arquivos Excel
- **pandas** - Análise e manipulação de dados
- **pymongo** - Driver MongoDB (via djongo)
- **djongo** - Django + MongoDB
- **requests** - Cliente HTTP
- **aiohttp** - Cliente HTTP assíncrono

## 🚀 Instalação

### **🏠 Desenvolvimento Local (Windows)**

#### **Pré-requisitos**
- Python 3.7 ou superior
- pip (gerenciador de pacotes Python)
- Git (opcional, para clonar o repositório)

#### **Passo a Passo**

1. **Clone o repositório**
   ```bash
   git clone https://github.com/thsteixeira/precatorios.git
   cd precatorios
   ```

2. **Configure o ambiente local (simplificado)**
   ```bash
   # Use o script automático para configurar o ambiente local
   deployment\scripts\switch_env.bat local
   
   # Ou configure manualmente:
   copy deployment\environments\.env.local .env
   ```
   
   ✅ **Não são necessárias variáveis de ambiente!**  
   Todas as configurações estão hardcoded para facilitar o desenvolvimento local.

3. **Crie um ambiente virtual**
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

4. **Instale as dependências**
   ```bash
   pip install -r requirements.txt
   ```

5. **Execute as migrações**
   ```bash
   python manage.py migrate
   ```

6. **Crie um superusuário (opcional)**
   ```bash
   python manage.py createsuperuser
   ```

7. **Execute o servidor de desenvolvimento**
   ```bash
   python manage.py runserver
   ```

8. **Acesse a aplicação**
   ```
   http://127.0.0.1:8000/
   ```

### **🏗️ Deployment Multi-Ambiente (Produção)**

Este projeto possui um **sistema completo de deployment multi-ambiente** com:

#### **📁 Estrutura de Deployment**
```
deployment/
├── docs/                          # Documentação completa
│   ├── README.md                  # Guia principal
│   ├── ENVIRONMENT_SETUP.md       # Setup detalhado
│   └── AWS_S3_SETUP.md           # Configuração S3
├── environments/                  # Templates de ambiente
│   ├── .env.local                # Local (Windows + SQLite)
│   ├── .env.test                 # Test (EC2 + PostgreSQL + S3)
│   └── .env.production           # Production (EC2 + PostgreSQL + S3)
└── scripts/                      # Scripts de automação
    ├── switch_env.bat/.sh        # Troca de ambiente
    ├── deploy_test.sh            # Deploy teste (completo)
    └── deploy_production.sh      # Deploy produção (completo)
```

#### **🌟 Ambientes Disponíveis**

| Ambiente | Plataforma | Database | Storage | Uso |
|----------|------------|----------|---------|-----|
| **Local** | Windows | SQLite | Local | Desenvolvimento |
| **Test** | EC2 Ubuntu | PostgreSQL | AWS S3 | Testes |
| **Production** | EC2 Ubuntu | PostgreSQL | AWS S3 | Produção |

#### **⚡ Quick Start - Deployment**

**Para Test Environment:**
```bash
# No servidor EC2 Ubuntu
git clone https://github.com/thsteixeira/precatorios.git
cd precatorios
chmod +x deployment/scripts/deploy_test.sh
./deployment/scripts/deploy_test.sh
```

**Para Production Environment:**
```bash
# No servidor EC2 Ubuntu (com domínio configurado)
export PRODUCTION_DOMAIN_OR_IP="seu-dominio.com"
chmod +x deployment/scripts/deploy_production.sh
./deployment/scripts/deploy_production.sh
```

#### **🔧 Recursos dos Scripts de Deploy**

**Deploy Test & Production incluem:**
- ✅ **Setup completo do sistema** (Nginx + Gunicorn + systemd)
- ✅ **Configuração automática de SSL** (Let's Encrypt para produção)
- ✅ **Detecção inteligente de S3** (serve media do S3 se configurado)
- ✅ **Firewall e segurança** (UFW + Fail2ban para produção)
- ✅ **Backup automatizado** (scripts de backup diário)
- ✅ **Monitoramento e logs** (rotação automática de logs)
- ✅ **Health checks** (validação completa do deployment)

#### **📖 Documentação Detalhada**

📁 **[deployment/docs/README.md](deployment/docs/README.md)** - Guia completo de deployment  
📁 **[deployment/docs/ENVIRONMENT_SETUP.md](deployment/docs/ENVIRONMENT_SETUP.md)** - Setup detalhado  
📁 **[deployment/docs/AWS_S3_SETUP.md](deployment/docs/AWS_S3_SETUP.md)** - Configuração AWS S3

### **🔄 Troca de Ambiente (Local)**

```bash
# Trocar para ambiente local
deployment\scripts\switch_env.bat local

# Trocar para teste (simulação)
deployment\scripts\switch_env.bat test

# Trocar para produção (simulação)
deployment\scripts\switch_env.bat production
```

## 🏗️ Arquitetura Multi-Ambiente

### **⚙️ Configuração Inteligente**

O sistema utiliza **configuração automática baseada no ambiente**:

```python
# settings.py detecta automaticamente o ambiente
ENVIRONMENT = config('ENVIRONMENT', default='local')

if ENVIRONMENT == 'local':
    # Configurações hardcoded para desenvolvimento
    DEBUG = True
    DATABASE = SQLite
    MEDIA_STORAGE = Local
else:
    # Configurações via variáveis de ambiente
    DEBUG = config('DEBUG', cast=bool)
    DATABASE = PostgreSQL  
    MEDIA_STORAGE = AWS_S3
```

### **🎯 Características por Ambiente**

#### **🏠 Local (Windows)**
- ✅ **Zero configuração** - settings hardcoded
- ✅ **SQLite database** - sem dependências externas
- ✅ **Local file storage** - arquivos na pasta media/
- ✅ **Debug ativo** - para desenvolvimento
- ✅ **Hot reload** - mudanças instantâneas

#### **🧪 Test (EC2)**
- ✅ **PostgreSQL** - database robusto
- ✅ **AWS S3** - storage escalável
- ✅ **Nginx + Gunicorn** - setup de produção
- ✅ **SSL opcional** - para testes HTTPS
- ✅ **Environment variables** - configuração segura

#### **🚀 Production (EC2)**
- ✅ **PostgreSQL** - alta performance
- ✅ **AWS S3** - storage distribuído
- ✅ **SSL/HTTPS obrigatório** - Let's Encrypt automático
- ✅ **Firewall + Fail2ban** - segurança avançada
- ✅ **Backup automatizado** - proteção de dados
- ✅ **Log rotation** - gestão de logs
- ✅ **Health monitoring** - monitoramento contínuo

### **🔧 Recursos Avançados**

#### **📦 Deploy com Um Comando**
```bash
# Deploy completo em segundos
./deployment/scripts/deploy_production.sh

# Inclui automaticamente:
# - Sistema operacional atualizado
# - Python + dependências
# - Nginx + SSL + Gunicorn
# - Database + migrações
# - S3 + static files
# - Firewall + segurança
# - Backup + monitoring
```

#### **🔄 Detecção Inteligente de S3**
```nginx
# Nginx configurado automaticamente baseado em USE_S3
location /media/ {
    # Se S3=true: não inclui esta seção
    # Se S3=false: serve arquivos localmente
    alias /var/www/precatorios/media/;
}
```

#### **🛡️ Segurança Automática (Produção)**
- **SSL/TLS**: Certificados Let's Encrypt automáticos
- **Headers de Segurança**: HSTS, CSP, XSS Protection
- **Rate Limiting**: Proteção contra ataques
- **Firewall**: UFW configurado automaticamente
- **Fail2ban**: Proteção contra brute force
- **Secret Key**: Geração automática para produção

### **📊 Monitoramento e Logs**

```bash
# Logs centralizados por ambiente
/var/log/precatorios/
├── django.log              # Application logs
├── gunicorn_access.log     # HTTP access logs
├── gunicorn_error.log      # Application errors
└── nginx_access.log        # Web server logs

# Comandos de monitoramento
sudo journalctl -u gunicorn_precatorios_production -f  # Live logs
sudo systemctl status nginx                            # Service status
curl https://seu-dominio.com/health/                  # Health check
```

### **Comandos Úteis**

```bash
# Executar testes
python manage.py test

# Criar um administrador
python manage.py create_admin

# Importar dados do Excel
python manage.py import_excel caminho/para/arquivo.xlsx

# Atualizar prioridades por idade
python manage.py update_priority_by_age

# Acessar o shell Django
python manage.py shell

# Verificar problemas no projeto
python manage.py check
```

## 📖 Uso

### **Login**
1. Acesse `http://127.0.0.1:8000/login/`
2. Faça login com suas credenciais
3. Será redirecionado para o dashboard principal

### **Navegação Principal**
- **Dashboard**: Visão geral com estatísticas
- **Precatórios**: Lista e gestão de precatórios
- **Clientes**: Lista e gestão de clientes
- **Alvarás**: Lista e gestão de alvarás
- **Requerimentos**: Lista e gestão de requerimentos
- **Tipos de Precatórios**: Gestão de categorias de precatórios
- **Tipos de Diligências**: Gestão de tipos de diligências
- **Fases**: Configuração de fases processuais
- **Customização**: Configurações do sistema

### **Fluxo Típico de Uso**
1. **Configurar Tipos**: Defina tipos de precatórios (Alimentar, Comum, etc.)
2. **Criar um Precatório**: Cadastre um novo precatório com CNJ, valores e tipo
3. **Adicionar Cliente**: Vincule clientes ao precatório
4. **Gerenciar Alvarás**: Cadastre alvarás relacionados ao precatório
5. **Controlar Requerimentos**: Acompanhe pedidos e fases processuais
6. **Monitorar Status**: Use o dashboard para acompanhar o progresso
7. **Gerenciar Diligências**: Acompanhe e gerencie diligências por tipo

## 📁 Estrutura do Projeto

```
precatorios/
├── manage.py                 # Script de gerenciamento Django
├── db.sqlite3               # Banco de dados SQLite
├── requirements.txt         # Dependências do projeto
├── .gitignore              # Arquivos ignorados pelo Git
├── README.md               # Este arquivo
├── precatorios/            # Configurações do projeto
│   ├── __init__.py
│   ├── settings.py         # Configurações Django
│   ├── urls.py            # URLs principais
│   ├── wsgi.py            # Interface WSGI
│   └── asgi.py            # Interface ASGI
└── precapp/               # Aplicação principal
    ├── __init__.py
    ├── admin.py           # Configurações do Django Admin
    ├── apps.py            # Configuração da app
    ├── models.py          # Modelos de dados
    ├── views.py           # Views/Controllers
    ├── urls.py            # URLs da aplicação
    ├── forms.py           # Formulários Django
    ├── migrations/        # Migrações do banco de dados
    ├── templates/         # Templates HTML
    │   ├── base.html
    │   ├── registration/
    │   │   └── login.html
    │   └── precapp/
    │       ├── home.html
    │       ├── precatorio_*.html
    │       ├── cliente_*.html
    │       ├── alvara_*.html
    │       ├── requerimento_*.html
    │       ├── tipo_*.html           # NEW: Templates para tipos
    │       ├── tipos_*.html          # NEW: Templates para listas de tipos
    │       └── confirmar_delete_tipo_*.html  # NEW: Templates de confirmação
    ├── static/            # Arquivos estáticos
    │   └── precapp/
    │       └── js/
    │           └── brazilian-number-format.js
    ├── tests/             # NEW: Estrutura modularizada de testes
    │   ├── __init__.py
    │   ├── test_models.py      # Testes dos modelos
    │   ├── test_forms.py       # Testes dos formulários
    │   ├── test_views.py       # Testes das views principais
    │   ├── test_edge_cases.py  # Testes de casos extremos
    │   ├── test_verification.md # Documentação de verificação
    │   └── views/              # NEW: Testes específicos de views
    │       ├── __init__.py
    │       └── test_tipo_views.py  # NEW: Testes específicos dos tipos
    └── management/        # Comandos customizados
        └── commands/
            ├── populate_db.py
            ├── create_admin.py
            ├── import_excel.py
            └── update_priority_by_age.py
```

## 🗄️ Modelos de Dados

### **Tipo**
```python
- nome (CharField, Unique) - Nome único do tipo de precatório
- descricao (TextField) - Descrição opcional detalhada
- cor (CharField) - Código hexadecimal para identificação visual (ex: #007bff)
- ordem (PositiveIntegerField) - Ordem de exibição (menores aparecem primeiro)
- ativa (BooleanField) - Status de ativação do tipo
- criado_em (DateTimeField) - Timestamp de criação automática
- atualizado_em (DateTimeField) - Timestamp de atualização automática
```

### **Precatorio**
```python
- cnj (CharField, PK) - Número CNJ do processo
- data_oficio (DateField) - Data do ofício
- orcamento (IntegerField) - Ano do orçamento
- valor_de_face (DecimalField) - Valor original
- ultima_atualizacao (DecimalField) - Valor atualizado
- percentuais contratuais e sucumbenciais
- status de pagamento (credito_principal, honorarios_contratuais, honorarios_sucumbenciais)
- tipo (ForeignKey) - NEW: Referência ao tipo de precatório
```

### **Cliente**
```python
- cpf (CharField, PK) - CPF do cliente
- nome (CharField) - Nome completo
- nascimento (DateField) - Data de nascimento
- prioridade (BooleanField) - Se possui prioridade legal
```

### **Alvara**
```python
- cliente (ForeignKey) - Cliente associado
- precatorio (ForeignKey) - Precatório associado  
- tipo/fase (CharField) - Status do alvará
- valores financeiros (DecimalField) - Principal, contratuais, sucumbenciais
```

### **Requerimento**
```python
- cliente (ForeignKey) - Cliente associado
- precatorio (ForeignKey) - Precatório associado
- pedido (CharField) - Tipo de pedido
- valor (DecimalField) - Valor do requerimento
- desagio (DecimalField) - Percentual de deságio
- fase (CharField) - Fase processual
```

### **Fase**
```python
- nome (CharField) - Nome da fase
- descricao (TextField) - Descrição opcional
- cor (CharField) - Código hexadecimal para identificação visual
- tipo (CharField) - Tipo da fase (alvará, requerimento, ambos)
- ordem (PositiveIntegerField) - Ordem de exibição
- ativa (BooleanField) - Status de ativação
```

### **TipoDiligencia**
```python
- nome (CharField, Unique) - Nome único do tipo de diligência
- descricao (TextField) - Descrição opcional
- cor (CharField) - Código hexadecimal para identificação visual
- ordem (PositiveIntegerField) - Ordem de exibição
- ativo (BooleanField) - Status de ativação
```

## 📸 Screenshots

*[Adicione screenshots da aplicação aqui]*

### Dashboard Principal
![Dashboard](screenshots/dashboard.png)

### Lista de Precatórios
![Precatórios](screenshots/precatorios.png)

### Detalhes do Cliente
![Cliente](screenshots/cliente.png)

## 🤝 Contribuição

Contribuições são bem-vindas! Para contribuir:

1. **Fork** o projeto
2. Crie uma **branch** para sua feature (`git checkout -b feature/AmazingFeature`)
3. **Commit** suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. **Push** para a branch (`git push origin feature/AmazingFeature`)
5. Abra um **Pull Request**

### **Diretrizes de Contribuição**
- Siga as convenções de código Python (PEP 8)
- Adicione testes para novas funcionalidades
- Atualize a documentação conforme necessário
- Use mensagens de commit descritivas

## 📋 TODO / Roadmap

### **🔄 Em Desenvolvimento**
- [x] **Sistema de Tipos de Precatórios** - Categorização visual completa ✅
- [x] **Sistema de Tipos de Diligências** - Gestão completa de tipos ✅
- [x] **Testes Abrangentes** - Cobertura completa de testes unitários ✅
- [x] **Estrutura Modular de Testes** - Organização avançada por componente ✅

### **🎯 Próximos Passos**
- [ ] **Containerização** - Configuração Docker para deploy
- [ ] **Relatórios PDF** - Geração de relatórios em PDF
- [ ] **Gráficos** - Dashboard com gráficos estatísticos
- [ ] **API REST** - Endpoints para integração externa
- [ ] **Notificações** - Sistema de alertas e lembretes
- [ ] **Backup automático** - Rotinas de backup do banco
- [ ] **Auditoria** - Log de alterações nos dados
- [ ] **Filtros avançados** - Busca e filtragem melhoradas

### **🚀 Melhorias Futuras**
- [ ] **Dashboard Analítico** - Gráficos por tipos de precatórios
- [ ] **Exportação Avançada** - Excel com formatação por tipos
- [ ] **Workflow Automatizado** - Transições automáticas de fases
- [ ] **Integração com API TJ** - Sincronização com sistemas oficiais
- [ ] **Mobile App** - Aplicativo móvel para consultas
- [ ] **Relatórios Personalizáveis** - Builder de relatórios
- [ ] **Sistema de Aprovações** - Workflow de aprovação multi-nível

## 🐛 Problemas Conhecidos

### **Solucionados Recentemente**
- ~~Alguns testes podem precisar de reorganização para melhor manutenibilidade~~ ✅ **RESOLVIDO** - Estrutura modular implementada
- ~~Falta sistema de categorização de precatórios~~ ✅ **RESOLVIDO** - Sistema de tipos implementado
- ~~Ausência de testes específicos para componentes críticos~~ ✅ **RESOLVIDO** - Cobertura de testes expandida

### **Questões Menores**
- Validação de CPF pode precisar de melhorias
- Interface responsiva pode ser otimizada para mobile
- Paginação não implementada em listas grandes

### **Melhorias de UX Identificadas**
- Filtros por tipos de precatórios podem ser expandidos
- Sistema de busca pode incluir busca por tipo
- Exportação pode incluir informações de tipos

## 🧪 Testes

O projeto inclui uma suíte abrangente de testes com estrutura modularizada localizada em `precapp/tests/`:

```bash
# Executar todos os testes
python manage.py test

# Executar testes com detalhes
python manage.py test -v 2

# Executar testes específicos
python manage.py test precapp.tests.test_models.TipoModelTest
python manage.py test precapp.tests.test_forms.TipoFormComprehensiveTest
python manage.py test precapp.tests.views.test_tipo_views.TipoPrecatorioViewsTest
```

### **📊 Cobertura de Testes**

#### **Modelos (test_models.py)**
- ✅ Modelos principais (Precatorio, Cliente, Alvara, Requerimento)
- ✅ **Tipo Model** - Validação, métodos de classe, ordenação
- ✅ Fase Model - Validações e tipos
- ✅ TipoDiligencia Model - CRUD e validações
- ✅ Relacionamentos entre modelos
- ✅ Validações de CPF/CNPJ e CNJ
- ✅ Casos extremos e edge cases

#### **Formulários (test_forms.py)**
- ✅ Formulários principais (PrecatorioForm, ClienteForm, etc.)
- ✅ **TipoForm** - 36 testes abrangentes incluindo validação, widgets, casos extremos
- ✅ Validação de campos obrigatórios
- ✅ Formatação brasileira
- ✅ Validações personalizadas
- ✅ Widgets e estilização Bootstrap

#### **Views (test_views.py + views/test_tipo_views.py)**
- ✅ Views principais com autenticação
- ✅ **Views de Tipos** - 36 testes específicos para todas as operações CRUD
- ✅ CRUD completo (Create, Read, Update, Delete)
- ✅ Filtros e buscas
- ✅ Segurança e autenticação
- ✅ Performance e otimização de queries

#### **Casos Extremos (test_edge_cases.py)**
- ✅ Validações limites
- ✅ Dados malformados
- ✅ Concorrência de dados
- ✅ **Testes específicos para tipos** incluindo casos limite

### **🎯 Estatísticas de Testes**
- **Total de Classes de Teste**: 8+ classes especializadas
- **Total de Métodos de Teste**: 150+ testes individuais
- **Cobertura de Tipos**: 72+ testes específicos para funcionalidade de tipos
- **Performance**: Testes de otimização de queries inclusos
- **Segurança**: Testes de autenticação e autorização

### **🔍 Testes Específicos da Funcionalidade de Tipos**

#### **TipoModelTest** (12 testes)
- Criação e validação de tipos
- Unicidade de nomes
- Valores padrão e ordenação
- Métodos de classe (get_tipos_ativos)
- Soft delete pattern

#### **TipoFormComprehensiveTest** (36 testes)
- Validação completa de campos
- Casos extremos e edge cases
- Widgets e estilização
- Performance e acessibilidade

#### **TipoPrecatorioViewsTest** (36 testes)
- CRUD completo de tipos
- Autenticação e autorização
- Filtros e buscas
- Performance e otimização

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 📞 Contato

**Desenvolvedor**: Thiago Teixeira
**Email**: [thsteixeira@gmail.com]
**Projeto**: [https://github.com/thsteixeira/precatorios.git](https://github.com/thsteixeira/precatorios.git)

---

### 🙏 Agradecimentos

- Django Community pela excelente documentação
- Bootstrap Team pelo framework CSS
- Font Awesome pela biblioteca de ícones
- Todos os contribuidores do projeto
- Comunidade Python Brasil pelo suporte e inspiração

### 📈 Histórico de Atualizações

#### **v2.0.0 - Agosto 2025** 🎨
- ✅ **Sistema Completo de Tipos de Precatórios**
- ✅ **Sistema de Tipos de Diligências** 
- ✅ **Estrutura Modular de Testes** (150+ testes)
- ✅ **Interface Visual Aprimorada** com cores personalizáveis
- ✅ **72+ Testes Específicos** para funcionalidade de tipos
- ✅ **Documentação Expandida** com cobertura completa

#### **v1.x - Versões Anteriores**
- ✅ Sistema base de precatórios, clientes, alvarás
- ✅ Sistema de fases e diligências
- ✅ Autenticação e interface base
- ✅ Validações brasileiras (CPF/CNPJ, CNJ)

---

**⭐ Se este projeto foi útil para você, considere dar uma estrela!**
