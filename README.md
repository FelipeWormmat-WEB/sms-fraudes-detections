# SMS Fraude Detection — Estrutura do Projeto

Este documento descreve a estrutura completa do repositório e apresenta, em uma linha, o propósito de cada diretório e arquivo. As descrições foram elaboradas a partir da árvore de arquivos atual e convenções de projeto.

## Visão Geral

- Projeto multi-serviço para detecção de fraude/spam em SMS
- Componentes:
  - gateway-service (Python, API/serviços, banco e ML)
  - classification-service (Go, serviço de classificação/auxiliar)
  - frontend (React + Vite + TypeScript + Tailwind)
  - datasets (conjuntos de dados CSV)
  - migrações e configuração Alembic
  - orquestração via Docker Compose

## Estrutura (nível superior)

- alembic/ — Configurações e templates Alembic (migrações de banco)
  - versions/ — Diretório para scripts de migração gerados pelo Alembic
  - env.py — Script de ambiente Alembic (configura engine, metadata e contexto)
  - README — Documento/placeholder do Alembic
  - script.py.mako — Template para criação de novas migrações
- classification-service/ — Serviço em Go
  - tests/
    - main_test.go — Testes automatizados do serviço em Go
  - Dockerfile — Dockerfile do serviço de classificação em Go
  - go.mod — Definições de módulo e dependências do serviço Go
  - go.sum — Hashes de dependências do serviço Go
  - main.go — Aplicação principal do serviço de classificação (servidor/handlers)
- database-service/ — Serviço de banco (estrutura base)
  - migrations/ — Diretório reservado para migrações do banco deste serviço
- datasets/ — Conjuntos de dados utilizados no treinamento/avaliação
  - CEAS_08.csv — Dataset CSV
  - SMSSpamCollection.csv — Dataset clássico de SMS spam
  - spam(in).csv — Outro dataset CSV de spam
- frontend/ — Aplicação web (React + Vite + TS + Tailwind)
  - public/
    - vite.svg — Ícone padrão do Vite
  - src/
    - assets/
      - react.svg — Ícone/asset do React
    - styles/
      - theme.css — Estilos globais/tema
    - App.css — Estilos do componente App
    - App.tsx — Componente raiz da SPA
    - index.css — Estilos globais
    - main.tsx — Ponto de entrada da aplicação React/TS (bootstrap do app)
  - .gitignore — Arquivos/padrões ignorados pelo Git
  - eslint.config.js — Configuração do ESLint
  - index.html — HTML host do app Vite
  - package.json — Metadados do projeto frontend e dependências NPM
  - postcss.config.js — Configuração do PostCSS
  - README.md — Documentação do frontend
  - tailwind.config.js — Configuração do TailwindCSS
  - tsconfig.app.json — Configuração TS específica do app
  - tsconfig.json — Configuração TypeScript base
  - tsconfig.node.json — Configuração TS para ambiente Node
  - vite.config.ts — Configuração do Vite
- gateway-service/ — Serviço gateway (Python: API, DB, ML)
  - alembic/
    - versions/ — Diretório para scripts de migração do gateway
    - env.py — Configuração do Alembic para o gateway-service
  - app/
    - api/
      - __init__.py — Inicialização do pacote api
      - endpoints.py — Rotas/handlers da API (p.ex. classificação, health, etc.)
      - models.py — Modelos de domínio/DB ligados à camada API (separação lógica)
      - schemas.py — Esquemas Pydantic (validação/serialização de payloads)
    - core/
      - __init__.py — Inicialização do pacote core
      - config.py — Configurações do serviço (env vars, constantes)
      - security.py — Utilitários de segurança/autenticação/autorização
    - db/
      - __init__.py — Inicialização do pacote db
      - database.py — Configuração de conexão ao banco (engine, base)
      - models.py — Modelos ORM (provável SQLAlchemy) do domínio persistido
      - session.py — Criação/gerenciamento de sessões de banco
    - services/
      - classification.py — Lógica de classificação/predição utilizando o modelo
    - __init__.py — Inicialização do pacote app
    - main.py — Instancia/expõe a aplicação web (ex.: FastAPI) do gateway
  - tests/
    - test_gateway.py — Testes automatizados do gateway service
  - __init__.py — Marca o diretório como pacote Python
  - Dockerfile — Dockerfile do serviço gateway (build e runtime)
  - main.py — Script/entrypoint do serviço (pode inicializar o servidor)
  - requirements.txt — Dependências Python do gateway-service
  - schemas.py — Esquemas/DTOs compartilhados no nível do serviço (fora de app/)
  - train_model.py — Script de treinamento do modelo de classificação
  - utils.py — Funções utilitárias compartilhadas
- alembic.ini — Configuração raiz do Alembic
- docker-compose.yml — Orquestração dos serviços (containers, redes, volumes)
- go.mod — Módulo Go no nível do repositório (escopo raiz)
- go.sum — Hashes de dependências Go no nível do repositório
- requirements.txt — Dependências Python no nível do repositório

## Notas de Conteúdo e Papéis

- gateway-service/app/services/classification.py: implementação da lógica de classificação; tipicamente carrega um modelo treinado (via pickle/arquivo) e expõe funções para prever se uma mensagem é SPAM/Fraude.
- gateway-service/train_model.py: roteiro para treinar e possivelmente persistir o modelo (p.ex. scikit-learn) usando os datasets em /datasets.
- gateway-service/app/api/endpoints.py: define as rotas HTTP; espera-se endpoints como POST /predict, GET /health, entre outros.
- gateway-service/app/core/config.py: ponto central para configurações (leitura de variáveis de ambiente, URIs de banco, chaves, flags de debug).
- gateway-service/app/db/*: abstrações de banco de dados (engine, modelos ORM e sessão), utilizadas pelos endpoints e serviços.
- classification-service/main.go: serviço em Go, possivelmente com endpoints leves para classificação/healthcheck ou lógica auxiliar.
- frontend: SPA para interface do usuário; construída com Vite, React, TypeScript e Tailwind; consumir os endpoints do gateway.
- alembic/* e gateway-service/alembic/*: permitem criar e aplicar migrações de banco de dados de forma consistente entre ambientes.
- docker-compose.yml: descreve como subir os serviços (containers de gateway, classification-service, banco de dados, etc.).

## Datasets

- CEAS_08.csv, SMSSpamCollection.csv, spam(in).csv: arquivos CSV utilizados no treinamento/validação. O script de treinamento deve referenciá-los diretamente ou via configuração.

## Testes

- classification-service/tests/main_test.go: testes do serviço em Go.
- gateway-service/tests/test_gateway.py: testes do gateway em Python.

## Observações Importantes

- Há dois níveis de configuração Alembic (raiz e gateway-service/). O Alembic do gateway tende a ser o aplicado aos modelos ORM do gateway. O Alembic raiz pode oferecer utilidades/protótipos globais.
- O gateway-service contém dois arquivos main.py (um em gateway-service/ e outro em gateway-service/app/). Em projetos FastAPI é comum que gateway-service/app/main.py exponha a variável `app` (ex.: `FastAPI()`), enquanto gateway-service/main.py atua como script de bootstrap/execução (ou utilitário). Use o que a orquestração (Docker/Compose) referenciar como entrypoint.
- Existem arquivos go.mod/go.sum no nível do repositório e dentro de classification-service/, indicando múltiplos módulos Go. O build de cada serviço deve usar o go.mod correspondente ao seu diretório.
