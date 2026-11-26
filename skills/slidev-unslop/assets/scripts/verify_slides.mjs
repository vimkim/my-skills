import fs from 'node:fs'
import http from 'node:http'
import path from 'node:path'
import { createRequire } from 'node:module'
import { pathToFileURL } from 'node:url'

const ROOT = process.cwd()
const DIST_DIR = path.resolve(ROOT, 'dist')

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.gif': 'image/gif',
  '.webp': 'image/webp',
  '.woff2': 'font/woff2',
  '.woff': 'font/woff',
  '.json': 'application/json; charset=utf-8',
  '.ico': 'image/x-icon',
}

function parseArgs(argv) {
  let slides = process.env.TOTAL_SLIDES ? Number(process.env.TOTAL_SLIDES) : null
  let outDir = '.verify'
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--slides' && argv[i + 1]) {
      slides = Number(argv[++i])
    } else if (argv[i] === '--out-dir' && argv[i + 1]) {
      outDir = argv[++i]
    }
  }
  return { slides, outDir: path.resolve(ROOT, outDir) }
}

async function loadChromium() {
  const require = createRequire(path.join(ROOT, 'package.json'))
  const candidates = [process.env.PLAYWRIGHT_PKG, 'playwright', 'playwright-chromium'].filter(Boolean)
  for (const candidate of candidates) {
    try {
      const mod = require(candidate)
      if (mod?.chromium) return mod.chromium
    } catch {}
    try {
      const target = path.isAbsolute(candidate) ? pathToFileURL(candidate).href : candidate
      const mod = await import(target)
      if (mod?.chromium) return mod.chromium
    } catch {}
  }
  throw new Error(
    'Playwright not found. Install playwright or playwright-chromium, or set PLAYWRIGHT_PKG.',
  )
}

function startStaticServer() {
  if (!fs.existsSync(path.join(DIST_DIR, 'index.html'))) {
    throw new Error(`Missing ${path.join(DIST_DIR, 'index.html')}. Run npm run build first.`)
  }
  const server = http.createServer((req, res) => {
    const urlPath = decodeURIComponent((req.url || '/').split('?')[0])
    const rel = urlPath.replace(/^\/+/, '')
    let filePath = path.resolve(DIST_DIR, rel)

    if (filePath !== DIST_DIR && !filePath.startsWith(DIST_DIR + path.sep)) {
      res.writeHead(403)
      res.end('Forbidden')
      return
    }

    if (!fs.existsSync(filePath) || fs.statSync(filePath).isDirectory()) {
      if (path.extname(urlPath) !== '') {
        res.writeHead(404)
        res.end('Not Found')
        return
      }
      filePath = path.join(DIST_DIR, 'index.html')
    }

    const ext = path.extname(filePath).toLowerCase()
    res.writeHead(200, { 'Content-Type': MIME[ext] || 'application/octet-stream' })
    fs.createReadStream(filePath).pipe(res)
  })

  return new Promise((resolve, reject) => {
    server.on('error', reject)
    server.listen(0, '127.0.0.1', () => {
      const { port } = server.address()
      resolve({ server, baseUrl: `http://127.0.0.1:${port}` })
    })
  })
}

const { slides: explicitTotal, outDir } = parseArgs(process.argv.slice(2))
fs.mkdirSync(outDir, { recursive: true })

const chromium = await loadChromium()
const { server, baseUrl } = await startStaticServer()

try {
  const browser = await chromium.launch({ headless: true })
  const context = await browser.newContext({ viewport: { width: 1280, height: 720 } })
  const page = await context.newPage()

  const pageErrors = []
  const consoleErrors = []

  page.on('pageerror', err => {
    if (!err.message.includes('Wake Lock')) pageErrors.push(err.message)
  })
  page.on('console', msg => {
    if (msg.type() === 'error') {
      const txt = msg.text()
      if (!txt.includes('/media/')) consoleErrors.push(txt)
    }
  })

  const maxSlides = explicitTotal || 200
  const report = []

  for (let i = 1; i <= maxSlides; i++) {
    await page.goto(`${baseUrl}/${i}`, { waitUntil: 'networkidle' })
    await page.waitForTimeout(350)

    if (!explicitTotal && i > 1) {
      const currentUrl = new URL(page.url())
      const expectedPath = `/${i}`
      if (currentUrl.pathname !== expectedPath && currentUrl.hash !== `#${expectedPath}`) {
        break
      }
    }

    const metrics = await page.evaluate((slideNum) => {
      const activePage =
        document.querySelector(`.slidev-page-${slideNum}`) ||
        Array.from(document.querySelectorAll('.slidev-layout')).find(el => {
          const r = el.getBoundingClientRect()
          return r.width > 0 && r.height > 0
        }) ||
        document.body

      const imgs = Array.from(activePage.querySelectorAll('img'))
      const brokenRequiredImgs = imgs
        .filter(img => img.dataset.optionalMedia !== 'true')
        .filter(img => !img.complete || img.naturalWidth === 0)
        .map(img => img.getAttribute('src'))

      const layoutEl = activePage.classList.contains('slidev-layout')
        ? activePage
        : (activePage.querySelector('.slidev-layout') || activePage)
      const rect = layoutEl.getBoundingClientRect()

      return {
        brokenRequiredImgs,
        scrollHeight: layoutEl.scrollHeight,
        clientHeight: layoutEl.clientHeight,
        overflowY: layoutEl.scrollHeight - layoutEl.clientHeight,
        overflowX: layoutEl.scrollWidth - layoutEl.clientWidth,
        rectHeight: Math.round(rect.height),
      }
    }, i)

    const outPath = path.join(outDir, `slide-${String(i).padStart(2, '0')}.png`)
    await page.screenshot({ path: outPath })
    report.push({ slide: i, ...metrics })
  }

  await browser.close()
  console.log(JSON.stringify({ totalSlides: report.length, pageErrors, consoleErrors, report }, null, 2))

  const hasFailure =
    report.length === 0 ||
    pageErrors.length > 0 ||
    consoleErrors.length > 0 ||
    report.some(r => r.brokenRequiredImgs.length > 0 || r.overflowY > 4 || r.overflowX > 4)

  if (hasFailure) process.exitCode = 1
} finally {
  server.closeAllConnections?.()
  server.close()
}
