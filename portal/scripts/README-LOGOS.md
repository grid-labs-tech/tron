# 🎨 Gerador de Logos PNG - Tron Platform

Este diretório contém ferramentas para gerar logos PNG em diversos tamanhos.

## ⚡ Método 1: Usando o Gerador HTML (Recomendado - Não requer instalação)

**A forma mais fácil e rápida!**

1. Abra o arquivo `generate-logo-pngs.html` no seu navegador
   ```bash
   # No macOS/Linux:
   open scripts/generate-logo-pngs.html

   # Ou simplesmente arraste o arquivo para o navegador
   ```

2. Clique nos botões "Download PNG" abaixo de cada logo
3. Os arquivos PNG serão baixados automaticamente na pasta de Downloads

## 🔧 Método 2: Usando o Script Node.js (Requer instalação)

### Pré-requisitos

```bash
cd portal
npm install sharp --save-dev
```

### Executar

```bash
npm run generate-logos
```

Os PNGs serão gerados em `portal/public/logos/`

## 📐 Tamanhos Gerados

- `favicon.png` - 16×16px (favicon do navegador)
- `icon-32.png` - 32×32px
- `icon-64.png` - 64×64px
- `icon-128.png` - 128×128px
- `icon-256.png` - 256×256px
- `icon-512.png` - 512×512px
- `logo-small.png` - 100×100px
- `logo-medium.png` - 200×200px
- `logo-large.png` - 400×400px
- `logo-xlarge.png` - 800×800px

## 🎯 Design do Logo

O logo é um cubo 3D isométrico estilizado que representa:
- **Infraestrutura**: As três faces do cubo representam diferentes camadas
- **Plataforma**: A estrutura sólida e confiável
- **Tecnologia**: Design moderno e sofisticado

Cores: Gradiente primário (índigo #6366f1 → roxo #8b5cf6)
