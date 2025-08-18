# 🏛️ Sistema de Controle de Precatórios

Um sistema web desenvolvido em Django para gerenciar precatórios judiciários, clientes, alvarás e requerimentos de forma eficiente e organizada.

![Django](https://img.shields.io/badge/Django-3.1.12-green?style=flat-square&logo=django)
![Python](https://img.shields.io/badge/Python-3.x-blue?style=flat-square&logo=python)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3.0-purple?style=flat-square&logo=bootstrap)
![SQLite](https://img.shields.io/badge/Database-SQLite-lightblue?style=flat-square&logo=sqlite)

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

## 🚀 Instalação

### **Pré-requisitos**
- Python 3.7 ou superior
- pip (gerenciador de pacotes Python)
- Git (opcional, para clonar o repositório)

### **Passo a Passo**

1. **Clone o repositório**
   ```bash
   git clone https://github.com/seu-usuario/precatorios.git
   cd precatorios
   ```

2. **Crie um ambiente virtual**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Instale as dependências**
   ```bash
   pip install django==3.1.12
   # Adicione outras dependências conforme necessário
   ```

4. **Execute as migrações**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Crie um superusuário (opcional)**
   ```bash
   python manage.py createsuperuser
   ```

6. **Popule o banco com dados de exemplo (opcional)**
   ```bash
   python manage.py populate_db
   ```

7. **Execute o servidor de desenvolvimento**
   ```bash
   python manage.py runserver
   ```

8. **Acesse a aplicação**
   ```
   http://127.0.0.1:8000/
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

### **Fluxo Típico de Uso**
1. **Criar um Precatório**: Cadastre um novo precatório com CNJ e valores
2. **Adicionar Cliente**: Vincule clientes ao precatório
3. **Gerenciar Alvarás**: Cadastre alvarás relacionados ao precatório
4. **Controlar Requerimentos**: Acompanhe pedidos e fases processuais
5. **Monitorar Status**: Use o dashboard para acompanhar o progresso

## 📁 Estrutura do Projeto

```
precatorios/
├── manage.py                 # Script de gerenciamento Django
├── db.sqlite3               # Banco de dados SQLite
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
    ├── tests.py           # Testes automatizados
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
    │       └── requerimento_*.html
    └── management/        # Comandos customizados
        └── commands/
            ├── populate_db.py
            └── create_admin.py
```

## 🗄️ Modelos de Dados

### **Precatorio**
```python
- cnj (CharField, PK) - Número CNJ do processo
- data_oficio (DateField) - Data do ofício
- orcamento (IntegerField) - Ano do orçamento
- valor_de_face (DecimalField) - Valor original
- ultima_atualizacao (DecimalField) - Valor atualizado
- percentuais contratuais e sucumbenciais
- status (quitado, acordo_deferido)
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

- [ ] **Relatórios PDF** - Geração de relatórios em PDF
- [ ] **Gráficos** - Dashboard com gráficos estatísticos
- [ ] **API REST** - Endpoints para integração externa
- [ ] **Notificações** - Sistema de alertas e lembretes
- [ ] **Backup automático** - Rotinas de backup do banco
- [ ] **Deploy** - Configuração para produção (Docker/Heroku)
- [ ] **Auditoria** - Log de alterações nos dados
- [ ] **Filtros avançados** - Busca e filtragem melhoradas

## 🐛 Problemas Conhecidos

- Validação de CPF pode precisar de melhorias
- Interface responsiva pode ser otimizada para mobile
- Paginação não implementada em listas grandes

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 📞 Contato

**Desenvolvedor**: [Seu Nome]
**Email**: [seu-email@exemplo.com]
**Projeto**: [https://github.com/seu-usuario/precatorios](https://github.com/seu-usuario/precatorios)

---

### 🙏 Agradecimentos

- Django Community pela excelente documentação
- Bootstrap Team pelo framework CSS
- Font Awesome pela biblioteca de ícones
- Todos os contribuidores do projeto

---

**⭐ Se este projeto foi útil para você, considere dar uma estrela!**
