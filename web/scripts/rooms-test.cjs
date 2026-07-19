const { chromium } = require("playwright");
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
  await page.addInitScript(() => sessionStorage.setItem("innsight-entered", "1"));
  await page.goto("http://localhost:3000/", { waitUntil: "networkidle" });
  await page.waitForTimeout(3000);
  const gs = page.getByRole("button", { name: "Get Started" });
  if (await gs.count()) { await gs.first().click(); }
  await page.waitForTimeout(3000);
  const place = page.getByText(/Place building/);
  if (await place.count()) { await place.first().click(); await page.waitForTimeout(2000); }
  await page.waitForSelector("text=Rooms:", { timeout: 20000 });
  const dir = "/tmp/claude-1000/-mnt-c-Users-minif-Downloads-UofT-Projects-hack-the-6IX/a44ecb3e-17eb-47ec-9f4f-d248d27a0516/scratchpad";
  const slider = page.locator('input[type="range"]').first();
  await slider.fill("10");
  await page.waitForTimeout(2000);
  await page.screenshot({ path: `${dir}/rooms-10.png` });
  await slider.fill("80");
  await page.waitForTimeout(2000);
  await page.screenshot({ path: `${dir}/rooms-80.png` });
  await browser.close();
  console.log("shots saved");
})().catch(e => { console.error("FAIL:", e.message); process.exit(1); });
