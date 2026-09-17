import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const projectRoot = path.resolve(__dirname, '..');

const templatePath = path.resolve(projectRoot, 'dist/index.html');
const serverEntryPath = path.resolve(projectRoot, 'dist-server/entry-server.js');

if (!fs.existsSync(templatePath)) {
  console.error(`[prerender] Template not found at ${templatePath}. Run 'vite build' first.`);
  process.exit(1);
}

if (!fs.existsSync(serverEntryPath)) {
  console.error(`[prerender] Server entry not found at ${serverEntryPath}. Run 'vite build --ssr' first.`);
  process.exit(1);
}

async function runPrerender() {
  console.log('[prerender] Starting static HTML generation for all routes...');
  const template = fs.readFileSync(templatePath, 'utf-8');

  // Dynamically import compiled server entry
  const { render, routes } = await import(pathToFileURL(serverEntryPath).href);

  // Collect all target routes, including 404
  const allRoutes = [...new Set([...routes, '/404'])];

  for (const url of allRoutes) {
    try {
      const { html, headTags } = render(url);

      // 1. Remove base title and description from template
      let routeHtml = template
        .replace(/<title>[\s\S]*?<\/title>/i, '')
        .replace(/<meta\s+name=["']description["'][\s\S]*?>/i, '');

      // 2. Inject route-specific head tags (title, description, canonical, OG, Twitter, JSON-LD)
      routeHtml = routeHtml.replace('</head>', `  ${headTags}\n  </head>`);

      // 3. Inject rendered React HTML into root
      routeHtml = routeHtml.replace(
        '<div id="root"></div>',
        `<div id="root">${html}</div>`
      );

      // 4. Determine output file path
      if (url === '/') {
        fs.writeFileSync(path.resolve(projectRoot, 'dist/index.html'), routeHtml, 'utf-8');
        console.log(`[prerender] Rendered: / -> dist/index.html`);
      } else if (url === '/404') {
        fs.writeFileSync(path.resolve(projectRoot, 'dist/404.html'), routeHtml, 'utf-8');
        console.log(`[prerender] Rendered: /404 -> dist/404.html`);
      } else {
        const routeSubdir = url.replace(/^\//, '');
        const targetDir = path.resolve(projectRoot, 'dist', routeSubdir);
        if (!fs.existsSync(targetDir)) {
          fs.mkdirSync(targetDir, { recursive: true });
        }
        // Write both directory index.html and root route.html for universal server & host support
        const dirIndexPath = path.resolve(targetDir, 'index.html');
        const fileHtmlPath = path.resolve(projectRoot, 'dist', `${routeSubdir}.html`);
        fs.writeFileSync(dirIndexPath, routeHtml, 'utf-8');
        fs.writeFileSync(fileHtmlPath, routeHtml, 'utf-8');
        console.log(`[prerender] Rendered: ${url} -> dist/${routeSubdir}/index.html & dist/${routeSubdir}.html`);
      }
    } catch (err) {
      console.error(`[prerender] Error rendering ${url}:`, err);
      process.exit(1);
    }
  }

  // Clean up temporary server build
  try {
    const distServerDir = path.resolve(projectRoot, 'dist-server');
    if (fs.existsSync(distServerDir)) {
      fs.rmSync(distServerDir, { recursive: true, force: true });
      console.log('[prerender] Cleaned up temporary dist-server artifacts.');
    }
  } catch (err) {
    console.warn('[prerender] Note: Could not remove dist-server:', err.message);
  }

  console.log('[prerender] Completed successfully! All static HTML routes generated.');
}

runPrerender();
