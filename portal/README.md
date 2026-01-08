# Tron Portal React

Portal web moderno para a plataforma Tron, construído com React, TypeScript e Tailwind CSS.

## Tecnologias

- **React 18** - Biblioteca UI
- **TypeScript** - Tipagem estática
- **Vite** - Build tool e dev server
- **Tailwind CSS** - Framework CSS utility-first
- **Lucide React** - Biblioteca de ícones
- **React Router** - Roteamento
- **React Query** - Gerenciamento de estado e cache de dados
- **Axios** - Cliente HTTP

## Estrutura do Projeto

```
portal/
├── src/
│   ├── components/     # Componentes reutilizáveis
│   ├── pages/          # Páginas da aplicação
│   ├── services/       # Serviços de API
│   ├── types/          # Definições TypeScript
│   ├── config/         # Configurações
│   ├── App.tsx         # Componente principal
│   └── main.tsx        # Entry point
├── public/             # Arquivos estáticos
├── package.json
└── vite.config.ts
```

## Desenvolvimento Local

### Pré-requisitos

- Node.js 20+
- npm ou yarn

### Instalação

```bash
cd portal
npm install
```

### Executar em desenvolvimento

```bash
npm run dev
```

A aplicação estará disponível em `http://localhost:3000`

### Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
VITE_API_BASE_URL=http://localhost:8000
```

## Build para Produção

```bash
npm run build
```

Os arquivos serão gerados na pasta `dist/`.

## Páginas Disponíveis

- **Home** (`/`) - Dashboard com estatísticas
- **Clusters** (`/clusters`) - Gerenciar clusters Kubernetes
- **Environments** (`/environments`) - Gerenciar environments
- **Webapps** (`/webapps`) - Gerenciar aplicações web
- **Namespaces** (`/namespaces`) - Gerenciar namespaces
- **Workloads** (`/workloads`) - Gerenciar tipos de workload

## Docker

O projeto inclui um Dockerfile para execução em containers. Para executar via Docker Compose:

```bash
make start
```

O portal React estará disponível em `http://localhost:3000`

## Scripts Disponíveis

- `npm run dev` - Inicia servidor de desenvolvimento
- `npm run build` - Build para produção
- `npm run preview` - Preview do build de produção
- `npm run lint` - Executa ESLint

