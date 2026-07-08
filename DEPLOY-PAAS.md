# Deploy em PaaS gerenciado

Topologia recomendada (sem administrar servidor):

- **Postgres gerenciado** pelo próprio PaaS.
- **Backend** (FastAPI) como serviço web via Docker — aplica migrations e cria o admin no boot ([entrypoint.sh](backend/entrypoint.sh)).
- **Frontend** (SPA Vite) como **site estático**, chamando a API em outro domínio.
- **Fotos de produto** em **disco persistente** anexado ao backend (simples, 1 instância).

O front resolve as imagens de `/uploads/...` no domínio da API via `assetUrl()` ([client.ts](frontend/src/api/client.ts)), então funciona mesmo com front e back em domínios diferentes.

---

## Render (recomendado) — via Blueprint

O [render.yaml](render.yaml) já declara os 3 componentes.

1. Suba o repositório no GitHub.
2. No Render: **New + → Blueprint** → selecione o repositório. Ele lê o `render.yaml`.
3. Preencha as variáveis marcadas como `sync: false` (o Render pergunta no deploy):
   - **estoque-backend**
     - `FIRST_ADMIN_EMAIL` e `FIRST_ADMIN_PASSWORD` — senha forte (troque depois do 1º login).
     - `BACKEND_CORS_ORIGINS` — a URL do frontend, ex.: `https://estoque-frontend.onrender.com`.
   - **estoque-frontend**
     - `VITE_API_BASE_URL` — a URL do backend + `/api/v1`, ex.: `https://estoque-backend.onrender.com/api/v1`.
4. Deploy. As URLs saem no formato `https://<nome>.onrender.com`.
5. Como o front precisa da URL do back (e vice-versa para o CORS), o fluxo é: primeiro deploy → copie as URLs → ajuste `VITE_API_BASE_URL` e `BACKEND_CORS_ORIGINS` → redeploy.
6. Faça login e **troque a senha do admin**.

`SECRET_KEY` é gerado automaticamente; `DATABASE_URL` vem do Postgres gerenciado; migrations rodam sozinhas no boot.

> Observações do plano gratuito: serviços web hibernam ociosos (cold start) e o Postgres free expira em 90 dias. Para produção, use planos pagos. O disco de uploads fixa o backend em 1 instância (troque para S3 se precisar escalar — ver abaixo).

---

## Railway (alternativa)

- Crie um projeto e adicione um **PostgreSQL** (plugin) → ele expõe `DATABASE_URL`.
- **Backend**: novo serviço a partir do repo, root `/backend`, build pelo `Dockerfile`. Variáveis: `ENVIRONMENT=production`, `DEBUG=false`, `SECRET_KEY` (gere um), `DATABASE_URL` (referência ao plugin, use o formato `postgresql+psycopg2://...` ou o `postgresql://` que o SQLAlchemy também aceita), `SEED_SAMPLE_DATA=false`, `BACKEND_CORS_ORIGINS` = URL do front. Anexe um **Volume** em `/app/uploads`.
- **Frontend**: serviço estático (ou Nixpacks) com build `npm ci && npm run build`, publish `dist`, variável `VITE_API_BASE_URL` = URL do back + `/api/v1`, e rewrite SPA `/* → /index.html`.

## Fly.io (alternativa)

- `fly postgres create` para o banco; anexe ao app do backend (injeta `DATABASE_URL`).
- Backend: `fly launch` na pasta `backend` (usa o `Dockerfile`), crie um **volume** e monte em `/app/uploads`; defina os secrets (`fly secrets set SECRET_KEY=... ENVIRONMENT=production DEBUG=false BACKEND_CORS_ORIGINS=...`).
- Frontend: outro app servindo `dist` (nginx ou `fly launch` estático) com `VITE_API_BASE_URL` no build.

---

## Checklist de produção

- [ ] `ENVIRONMENT=production`, `DEBUG=false` (o backend recusa subir em produção com `SECRET_KEY` padrão).
- [ ] `SECRET_KEY` forte e único (no Render é automático).
- [ ] Senha do primeiro admin forte; troque após o primeiro login.
- [ ] `SEED_SAMPLE_DATA=false`.
- [ ] `BACKEND_CORS_ORIGINS` = exatamente a URL do frontend (com `https://`, sem barra final).
- [ ] `VITE_API_BASE_URL` = URL do backend + `/api/v1`.
- [ ] HTTPS ativo (os PaaS já fornecem TLS nas URLs `*.onrender.com` etc.).
- [ ] Backup do Postgres (o plano gerenciado normalmente já faz; confirme a retenção).

---

## Uploads em escala (alternativa ao disco): S3/R2

O disco persistente atende 1 instância. Para múltiplas réplicas, troque o armazenamento local por object storage:

- Reescrever [storage.py](backend/app/core/storage.py) para enviar a `S3`/`Cloudflare R2` (via `boto3`) e retornar a URL pública do objeto (ou uma URL assinada).
- Remover o mount estático `/uploads` do [main.py](backend/app/main.py) (as imagens passam a ser servidas pelo storage).
- Adicionar as credenciais como variáveis de ambiente/secrets.

Posso implementar essa variante S3 se/quando for necessário escalar horizontalmente.
