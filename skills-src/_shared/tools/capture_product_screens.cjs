// No credentials, browser traces, HTML, or storage state are exported.
const fs = require('node:fs');
const path = require('node:path');
const {createHash} = require('node:crypto');
const [modulePath, planPath, out, mode, session] = process.argv.slice(2);
const {chromium, devices} = require(modulePath);
const plan = JSON.parse(fs.readFileSync(planPath, 'utf8'));
function target(value) {
  const url = new URL(value || '/', plan.baseUrl);
  if (!['http:', 'https:'].includes(url.protocol) || url.username || url.password)
    throw new Error('Invalid URL');
  if (url.origin !== new URL(plan.baseUrl).origin) throw new Error('Screen navigation must stay on the product origin');
  return url.href;
}
function publicUrl(value) {
  const url = new URL(value); url.search = ''; url.hash = ''; url.username = ''; url.password = '';
  return url.href;
}
async function steps(page, actions = []) {
  for (const step of actions) {
    const locator = page.locator(step.selector);
    switch (step.action) {
      case 'click': await locator.click(); break;
      case 'wait': await locator.waitFor({state: 'visible'}); break;
      case 'press': await locator.press(step.key); break;
      case 'fill': {
        const value = process.env[step.valueEnv];
        if (value === undefined) throw new Error('Missing environment variable');
        await locator.fill(value); break;
      }
      default: throw new Error('Unsupported step');
    }
  }
}
(async () => {
  const browser = await chromium.launch({headless: mode !== 'headed'});
  const assets = [];
  try {
    fs.mkdirSync(out, {recursive: true});
    for (const profile of plan.profiles || ['desktop']) {
      const options = profile === 'mobile'
        ? {...devices[plan.mobileDevice || 'iPhone 13']}
        : {viewport: plan.desktopViewport || {width: 1920, height: 1080}, deviceScaleFactor: 1};
      if (profile === 'mobile' && !options.isMobile) throw new Error('Unknown mobile device');
      if (session) options.storageState = session;
      const context = await browser.newContext(options);
      try {
        const page = await context.newPage();
        page.setDefaultTimeout(plan.timeoutMs || 30000);
        if (plan.login) {
          await page.goto(target(plan.login.url), {waitUntil: 'domcontentloaded'});
          await steps(page, plan.login.steps);
          // A headed run permits the user to complete MFA before this selector appears.
          await page.locator(plan.login.readySelector).waitFor({state: 'visible', timeout: plan.login.timeoutMs || 120000});
        }
        for (const screen of plan.screens) {
          await page.goto(target(screen.url), {waitUntil: 'domcontentloaded'});
          await steps(page, screen.steps);
          if (screen.readySelector) await page.locator(screen.readySelector).waitFor({state: 'visible'});
          await page.evaluate(() => document.fonts.ready);
          const file = `${screen.name}-${profile}.png`;
          const masks = [...(plan.maskSelectors || []), ...(screen.maskSelectors || []), 'input[type="password"]'].map(s => page.locator(s));
          const subject = screen.selector ? page.locator(screen.selector) : page;
          const buffer = await subject.screenshot({path: path.join(out, file), ...(screen.selector ? {} : {fullPage: screen.fullPage === true}), animations: 'disabled', mask: masks});
          assets.push({file, screen: screen.name, profile, sourceUrl: publicUrl(page.url()),
            viewport: options.viewport, device: profile === 'mobile' ? (plan.mobileDevice || 'iPhone 13') : 'desktop',
            alt: screen.alt || `${screen.name} product screen (${profile})`,
            capturedAt: new Date().toISOString(), sha256: createHash('sha256').update(buffer).digest('hex'),
            provenance: 'real-browser-capture', reviewRequired: true});
        }
      } finally { await context.close(); }
    }
    fs.writeFileSync(path.join(out, 'manifest.json'), JSON.stringify({schemaVersion: 1, assets}, null, 2));
    process.stdout.write(JSON.stringify({ready: true, manifest: path.join(out, 'manifest.json'), count: assets.length}));
  } finally { await browser.close(); }
})().catch(() => { process.stderr.write('Product capture failed; private browser details suppressed.\n'); process.exitCode = 1; });
