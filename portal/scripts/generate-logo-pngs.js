import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

// Try to import sharp
let sharp
try {
  const sharpModule = await import('sharp')
  sharp = sharpModule.default
} catch (error) {
  console.error('❌ Error: sharp is not installed.')
  console.error('   Run: npm install sharp --save-dev')
  console.error('   Or use the generate-logo-pngs.html file in the browser')
  process.exit(1)
}

// SVG do logo
const logoSvg = `
<svg width="200" height="200" viewBox="0 0 200 200" fill="none" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="logoGradient" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#6366f1;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#8b5cf6;stop-opacity:1" />
    </linearGradient>
  </defs>

  <!-- Cubo 3D isométrico -->
  <g transform="translate(100, 100)">
    <!-- Face superior -->
    <path
      d="M-60 -40L20 -80L100 -40L20 0L-60 -40Z"
      fill="url(#logoGradient)"
      opacity="0.9"
    />
    <!-- Face esquerda -->
    <path
      d="M-60 -40L20 0L20 80L-60 40L-60 -40Z"
      fill="url(#logoGradient)"
      opacity="0.7"
    />
    <!-- Face direita -->
    <path
      d="M20 0L100 -40L100 40L20 80L20 0Z"
      fill="url(#logoGradient)"
      opacity="0.8"
    />
    <!-- Linhas decorativas -->
    <path
      d="M20 -80L20 0M-60 -40L20 0M100 -40L20 0"
      stroke="white"
      stroke-width="3"
      stroke-linecap="round"
      opacity="0.5"
    />
  </g>
</svg>
`

// Tamanhos para gerar
const sizes = [
  { name: 'favicon', size: 16 },
  { name: 'icon-32', size: 32 },
  { name: 'icon-64', size: 64 },
  { name: 'icon-128', size: 128 },
  { name: 'icon-256', size: 256 },
  { name: 'icon-512', size: 512 },
  { name: 'logo-small', size: 100 },
  { name: 'logo-medium', size: 200 },
  { name: 'logo-large', size: 400 },
  { name: 'logo-xlarge', size: 800 },
]

// Diretório de saída
const outputDir = path.join(__dirname, '../public/logos')
if (!fs.existsSync(outputDir)) {
  fs.mkdirSync(outputDir, { recursive: true })
}

// Generate PNGs
async function generateLogos() {
  console.log('Generating PNG logos...\n')

  for (const { name, size } of sizes) {
    try {
      const outputPath = path.join(outputDir, `${name}.png`)

      await sharp(Buffer.from(logoSvg))
        .resize(size, size, {
          fit: 'contain',
          background: { r: 0, g: 0, b: 0, alpha: 0 }
        })
        .png()
        .toFile(outputPath)

      console.log(`✓ Generated: ${name}.png (${size}x${size})`)
    } catch (error) {
      console.error(`✗ Error generating ${name}.png:`, error.message)
    }
  }

  console.log(`\n✅ All logos have been generated in: ${outputDir}`)
}

generateLogos().catch(console.error)

