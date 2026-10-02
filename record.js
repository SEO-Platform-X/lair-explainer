const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: { width: 1920, height: 1080 }, recordVideo: { dir: 'out', size: { width: 1920, height: 1080 } } });
  const page = await ctx.newPage();
  await page.goto('file://' + process.cwd() + '/index.html?video=1', { waitUntil: 'networkidle' });
  await page.waitForSelector('body[data-done="1"]', { timeout: 150000 });
  await page.waitForTimeout(4500);
  await ctx.close(); await browser.close();
})();
