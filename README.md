# Sistema de Gestão de Estoque

Sistema web completo de gestão de estoque com foco em **rastreabilidade, auditoria, desempenho e manutenibilidade**. Backend em Python/FastAPI com arquitetura em camadas e frontend em React/TypeScript.

O saldo de estoque **nunca é editado manualmente** — é sempre derivado das movimentações registradas, garantindo consistência e histórico completo.

---

## Sumário

- [Arquitetura](#arquitetura)
- [Stack tecnológica](#stack-tecnológica)
- [Como executar](#como-executar)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Perfis e permissões](#perfis-e-permissões)
- [Regras de negócio](#regras-de-negócio)
- [Funcionalidades](#funcionalidades)
- [API](#api)
- [Testes e qualidade](#testes-e-qualidade)

---

## Arquitetura

Backend em **arquitetura em camadas** com responsabilidades bem separadas:

```
HTTP  →  Controller (API/routers)  →  Service (regras de negócio)  →  Repository (acesso a dados)  →  ORM/DB
                    │                          │                              │
                    │                          │                              └── SQLAlchemy 2.0 (models)
                    │                          └── auditoria, validações, orquestração
                    └── DTOs Pydantic, RBAC (require_permission), tratamento de erros
```

- **Controller** (`app/api`): endpoints FastAPI, validação de entrada/saída via schemas Pydantic (DTOs), guardas de permissão.
- **Service** (`app/services`): regras de negócio, transações, auditoria. Não conhece HTTP.
- **Repository** (`app/repositories`): toda a consulta ao banco. Um `BaseRepository` genérico + repositórios especializados.
- **Models** (`app/models`): entidades SQLAlchemy com índices, FKs e constraints.

O **frontend nunca acessa o banco diretamente** — toda comunicação passa pela API REST.

Princípios aplicados: **SOLID**, **Clean Architecture**, **Repository Pattern**, **Service Layer**, **DTOs**, tratamento centralizado de erros e logs estruturados (JSON).

---

## Stack tecnológica

| Camada | Tecnologias |
|--------|-------------|
| **Backend** | Python 3.12, FastAPI, SQLAlchemy 2.0, PostgreSQL, Alembic, Pydantic v2, JWT (python-jose), bcrypt |
| **Frontend** | React 18, TypeScript, Vite, Material UI, TanStack Query, React Hook Form, Zod, React Router, Recharts |
| **Exportação** | openpyxl (Excel), reportlab (PDF), CSV nativo |
| **Infra** | Docker, Docker Compose, Nginx, GitHub Actions (CI) |
| **Qualidade** | pytest, ruff, mypy, ESLint |

---

## Como executar

### Opção 1 — Docker Compose (recomendado)

Requisitos: Docker + Docker Compose.

```bash
cp .env.example .env          # ajuste as variáveis se desejar
docker compose up --build
```

Serviços:

| Serviço | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend (API) | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| PostgreSQL | localhost:5432 |

O backend, ao subir, **aguarda o banco**, aplica as **migrations do Alembic**, cria **permissões, perfis e usuário admin**, e (se `SEED_SAMPLE_DATA=true`) carrega **dados de demonstração**.

**Login padrão:** `admin` / `Admin@123`

### Opção 2 — Desenvolvimento local

**Backend:**

```bash
cd backend
python -m venv .venv && source .venv/Scripts/activate   # Windows Git Bash
pip install -r requirements-dev.txt

# Usando PostgreSQL local (ajuste POSTGRES_* no .env) ou SQLite para testes rápidos:
export DATABASE_URL="postgresql+psycopg2://estoque:estoque@localhost:5432/estoque"

alembic upgrade head          # cria as tabelas
python -m app.db.init_db      # cria permissões, perfis e admin
python -m app.db.sample_data  # (opcional) dados de demonstração

uvicorn app.main:app --reload
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev                   # http://localhost:5173 (proxy para :8000)
```

---

## Estrutura do projeto

```
sistemaEstoque/
├── backend/
│   ├── app/
│   │   ├── api/            # Controllers (routers) + deps (auth, RBAC)
│   │   ├── core/           # config, database, security, permissions, logging, errors
│   │   ├── models/         # Entidades SQLAlchemy
│   │   ├── schemas/        # DTOs Pydantic
│   │   ├── repositories/   # Camada de acesso a dados
│   │   ├── services/       # Regras de negócio + auditoria
│   │   ├── db/             # init_db (seed) e sample_data
│   │   └── main.py         # App FastAPI + handlers de erro + middleware
│   ├── alembic/            # Migrations
│   ├── tests/              # unit + integration (pytest)
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── api/            # client axios + endpoints tipados
│   │   ├── auth/           # AuthContext + ProtectedRoute
│   │   ├── components/     # Layout, DataGrid CRUD, etc.
│   │   ├── pages/          # Dashboard, Produtos, Movimentações, Inventário, ...
│   │   └── theme.ts
│   ├── Dockerfile + nginx.conf
├── .github/workflows/ci.yml
└── docker-compose.yml
```

---

## Perfis e permissões

Controle de acesso baseado em papéis (RBAC). Permissões no formato `recurso:ação`
(ex.: `product:create`, `inventory:approve`, `movement:cancel`).

| Perfil | Acesso |
|--------|--------|
| **Administrador** | Acesso total |
| **Supervisor** | Cadastros, movimentações, aprovação de inventários, relatórios, auditoria |
| **Operador** | Cadastro/edição de produtos, movimentações, contagem de inventário |
| **Somente Consulta** | Apenas leitura + dashboard/relatórios |

Cada endpoint é protegido por `require_permission("...")`. O frontend também oculta ações sem permissão.

---

## Regras de negócio

- ✅ **Saldo derivado exclusivamente das movimentações** — nunca editado manualmente.
- ✅ **Não permite saldo negativo** (configurável via `ALLOW_NEGATIVE_STOCK`).
- ✅ **Produtos com movimentação não podem ser excluídos** (apenas inativados).
- ✅ **Movimentações nunca são apagadas** — apenas canceladas, mantendo o histórico.
- ✅ **Produtos inativos não podem ser movimentados.**
- ✅ **Inventário aprovado gera ajustes automáticos** de estoque para cada divergência.
- ✅ **Toda alteração relevante gera registro de auditoria** (usuário, data, IP, campo, valor antigo/novo).
- ✅ **Múltiplos fornecedores por produto** com um principal e histórico de preços.
- ✅ **Múltiplas localizações** (corredores/prateleiras) com **saldo por local derivado das movimentações**.
- ✅ **Controle de validade** com alertas de vencimento próximo.
- ✅ **Movimentações concorrentes são seguras** — a linha do produto é bloqueada (`SELECT FOR UPDATE`), evitando venda além do saldo em condição de corrida.
- ✅ **Quantidades e valores usam `Decimal`** (sem erro de arredondamento de ponto flutuante).
- ✅ **Custo médio móvel ponderado** mantido a cada entrada, base da valorização de estoque.

---

## Funcionalidades

- **Autenticação JWT** com refresh token, **rotação de refresh** e **revogação no logout**.
- **Dashboard** com KPIs e gráficos (linha, barra, pizza, área) e **cache de curta duração**.
- **Produtos** com busca inteligente e **filtros avançados** (categoria, grupo, marca, fornecedor, status), **foto**, **importação via CSV** e tela de detalhe com abas (**fornecedores, lotes, localizações, histórico**).
- **Movimentações** de entrada/saída, transferência e cancelamento (mantendo histórico).
- **Inventário** com escopo configurável, contagem e ajuste automático na aprovação.
- **Central de Alertas**: abaixo do mínimo, sem estoque, próximos do vencimento e vencidos.
- **Cadastros**: categorias, grupos, subgrupos, marcas, corredores, prateleiras, fornecedores, usuários e **editor de perfis/permissões**.
- **Perfil do usuário** com troca de senha.
- **Auditoria** imutável e **Relatórios** exportáveis para **Excel, PDF e CSV**.
- **Interface totalmente responsiva** (desktop e mobile).

---

## Segurança e observabilidade

- **Proteção contra brute force**: rate limiting no login + **bloqueio de conta** após tentativas falhas.
- **Política de senha forte** (comprimento + maiúscula/minúscula/número/símbolo), validada no backend e no frontend.
- **Revogação de tokens** (denylist por `jti`) e **rotação de refresh token** com detecção de reuso.
- **Fail-fast em produção** se `SECRET_KEY` não for alterada.
- **Headers de segurança** no nginx (CSP, X-Frame-Options, etc.).
- **Métricas Prometheus** em `/metrics`, **readiness** em `/health/ready` (verifica o banco) e **Sentry** opcional (via `SENTRY_DSN`).
- **Logs estruturados JSON** com `X-Request-ID`.
- **Produção** servida por **Gunicorn + workers Uvicorn**.

---

## API

Documentação interativa (OpenAPI/Swagger) gerada automaticamente:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

São **52+ endpoints** sob o prefixo `/api/v1`. Exemplos:

```
POST   /api/v1/auth/login
GET    /api/v1/products?q=<termo>&category_id=&page=1&size=20
POST   /api/v1/movements
POST   /api/v1/movements/{id}/cancel
POST   /api/v1/inventories/{id}/approve
GET    /api/v1/dashboard
GET    /api/v1/reports/{report}/export?fmt=xlsx|pdf|csv
GET    /api/v1/audit
```

---

## Testes e qualidade

```bash
cd backend
pytest                      # testes unitários + integração
ruff check app tests        # lint
mypy app                    # type checking

cd ../frontend
npm run typecheck           # verificação de tipos
npm run build               # build de produção
npm run lint                # ESLint
```

A pipeline de **CI (GitHub Actions)** executa lint, testes e build para backend e frontend, além de validar o build das imagens Docker a cada push/PR.

---

## Variáveis de ambiente principais

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `SECRET_KEY` | Chave para assinatura JWT | *(troque em produção)* |
| `DATABASE_URL` | URL completa do banco (sobrepõe `POSTGRES_*`) | — |
| `ALLOW_NEGATIVE_STOCK` | Permitir saldo negativo | `false` |
| `EXPIRY_ALERT_DAYS` | Janela de alerta de vencimento (dias) | `30` |
| `FIRST_ADMIN_EMAIL` / `FIRST_ADMIN_PASSWORD` | Admin criado no bootstrap | `admin@estoque.com` / `Admin@123` |
| `SEED_SAMPLE_DATA` | Carregar dados de demonstração | `false` |

> **Segurança:** em produção, altere `SECRET_KEY` e a senha do admin, e defina `ENVIRONMENT=production` / `DEBUG=false`.
