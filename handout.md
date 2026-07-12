# Handout — Sistema de Gestão de Estoque

Guia rápido para **baixar, rodar localmente e demonstrar** o projeto em outro computador.
Para a documentação técnica completa (arquitetura, regras de negócio, API), veja o [README.md](README.md).

---

## 0. Levar o projeto para o outro computador

> ⚠️ **Este repositório ainda não tem um _remote_ configurado** (não há `origin`).
> Ou seja, o código está commitado **apenas neste PC** — não há um "main remoto" para clonar ainda.

Escolha **uma** das opções abaixo:

### Opção A — Publicar no GitHub (recomendado)
No computador atual:
```bash
# crie um repositório vazio no GitHub (github.com/new), depois:
git remote add origin https://github.com/<seu-usuario>/sistemaEstoque.git
git push -u origin main
```
No outro computador:
```bash
git clone https://github.com/<seu-usuario>/sistemaEstoque.git
cd sistemaEstoque
```

### Opção B — Cópia manual (pendrive / zip)
Copie a pasta **inteira** do projeto. Não é obrigatório levar a pasta `.git`, mas
**evite copiar** os artefatos pesados/gerados (eles são recriados):
`backend/.venv`, `frontend/node_modules`, `*.db`, `backend/uploads`.

---

## 1. Pré-requisitos

**Caminho recomendado (Docker):** apenas **Docker Desktop** (inclui Docker Compose).
É o jeito mais simples e reproduzível — sobe banco + backend + frontend com um comando.

**Caminho manual (sem Docker):** Python **3.12**, Node **18+** e, para banco real, PostgreSQL 16.

---

## 2. Rodar com Docker (recomendado para demonstração)

A partir da raiz do projeto:

```bash
cp .env.example .env
```

Abra o `.env` e **ative os dados de demonstração** (importante para a apresentação):

```env
SEED_SAMPLE_DATA=true
```

Suba tudo:

```bash
docker compose up --build
```

Na primeira vez o build demora alguns minutos. O backend aguarda o banco ficar
saudável, aplica as migrations do Alembic, cria permissões/perfis/admin e carrega
os dados de demonstração.

### Acessos

| Serviço | URL |
|---|---|
| **Aplicação (frontend)** | http://localhost:3000 |
| API (Swagger) | http://localhost:8000/docs |
| API (ReDoc) | http://localhost:8000/redoc |
| PostgreSQL | localhost:5432 |

### Login

```
usuário: admin
senha:   Admin@123
```

Para encerrar: `Ctrl+C` e depois `docker compose down`
(use `docker compose down -v` para apagar também o banco e começar do zero).

---

## 3. Rodar sem Docker (alternativa)

### Backend

```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate    # Windows Git Bash / PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
```

Escolha o banco via `DATABASE_URL`:

```bash
# PostgreSQL local:
export DATABASE_URL="postgresql+psycopg2://estoque:estoque@localhost:5432/estoque"

# OU SQLite (mais simples para uma demo rápida, sem instalar Postgres):
export DATABASE_URL="sqlite:///./estoque.db"
```

> 💡 **Se o PC usar Python 3.14**, o driver `psycopg2-binary` ainda não tem wheel
> para essa versão e a importação falha. Nesse caso **use a `DATABASE_URL` de SQLite**
> acima (a aplicação é agnóstica de banco) ou instale o Python 3.12.

Inicialize e rode:

```bash
alembic upgrade head          # cria as tabelas
python -m app.db.init_db      # permissões, perfis e admin
python -m app.db.sample_data  # (opcional) dados de demonstração
uvicorn app.main:app --reload # API em http://localhost:8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev                   # http://localhost:5173 (proxy para :8000)
```

Login: `admin` / `Admin@123`.

---

## 4. Roteiro sugerido de demonstração

Com `SEED_SAMPLE_DATA=true`, já existem categorias, produtos, clientes e pedidos.

1. **Login** com `admin` / `Admin@123`.
2. **Dashboard** — KPIs e gráficos (estoque, movimentações, valor de estoque).
3. **Produtos** — busca e filtros avançados; abra um produto e mostre as abas
   (fornecedores, lotes, localizações, histórico). Mostre a **importação via CSV**.
4. **Movimentações** — registre uma **entrada** e uma **saída**; tente uma saída
   maior que o saldo para mostrar que **saldo negativo é bloqueado**.
5. **Cancelamento de movimentação** — mostre que o histórico é mantido (nada é apagado).
6. **Inventário** — crie uma contagem, informe divergência e **aprove**: o ajuste
   de estoque é gerado automaticamente.
7. **Central de Alertas** — abaixo do mínimo, sem estoque, próximos do vencimento.
8. **Relatórios** — exporte para **Excel, PDF e CSV**.
9. **Auditoria** — mostre o registro imutável (usuário, data, IP, valor antigo/novo).
10. **Perfis e permissões** — abra o editor de perfis; logue como um perfil de
    menor acesso (ex.: *Somente Consulta*) para mostrar o RBAC ocultando ações.

> Dica: deixe o **Swagger** (`/docs`) aberto numa aba para mostrar que a API é
> documentada automaticamente e testável.

---

## 5. Verificação rápida (opcional)

```bash
# Backend
cd backend && pytest

# Frontend
cd frontend && npm run typecheck && npm run build
```

---

## 6. Problemas comuns

| Sintoma | Causa provável / solução |
|---|---|
| Porta 3000/8000/5432 já em uso | Feche o serviço que ocupa a porta ou ajuste o mapeamento no `docker-compose.yml`. |
| Dashboard vazio | Subiu sem `SEED_SAMPLE_DATA=true`. Rode `docker compose down -v` e suba de novo com a flag ativa. |
| `psycopg2` não importa (local) | Python 3.14 sem wheel — use `DATABASE_URL` de SQLite ou Python 3.12 (veja seção 3). |
| Frontend não fala com a API (local) | Confirme o backend em `:8000` e o `npm run dev` na porta `:5173` (proxy configurado). |
| Build Docker muito lento na 1ª vez | Normal — imagens e dependências são baixadas uma vez e ficam em cache. |
