// Renders every .svg in a folder to a transparent .png of the given size (default 512).
// usage: node tools/render_svg.js <dir> [size] [height]   (height defaults to size)
const fs = require("fs"), path = require("path");
const { chromium } = require("playwright");
(async () => {
  const dir = process.argv[2], size = parseInt(process.argv[3] || "512", 10);
  const height = parseInt(process.argv[4] || String(size), 10);
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: size, height: height } });
  for (const f of fs.readdirSync(dir).filter((f) => f.endsWith(".svg"))) {
    const svg = fs.readFileSync(path.join(dir, f), "utf8");
    await page.setContent(`<html><body style="margin:0;background:transparent">${svg.replace("<svg ", `<svg width="${size}" height="${height}" `)}</body></html>`);
    await page.screenshot({ path: path.join(dir, f.replace(/\.svg$/, ".png")), omitBackground: true, clip: { x: 0, y: 0, width: size, height: height } });
  }
  await browser.close();
})();
