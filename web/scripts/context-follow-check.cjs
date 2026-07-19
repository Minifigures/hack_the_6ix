// Regression check: translucent context buildings must follow the active site.
// Searches Mississauga and asserts a fresh /sites/context fetch for the new
// coordinates that returns real building features (not just the Toronto load).
const { chromium } = require("playwright");
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
  await page.addInitScript(() => sessionStorage.setItem("innsight-entered", "1"));

  const contextFetches = [];
  page.on("response", async (res) => {
    const url = res.url();
    if (!url.includes("/sites/context")) return;
    try {
      const u = new URL(url);
      const body = await res.json();
      contextFetches.push({
        lat: Number(u.searchParams.get("lat")),
        lng: Number(u.searchParams.get("lng")),
        features: (body.features || []).length,
      });
    } catch {}
  });

  await page.goto("http://localhost:3000/", { waitUntil: "networkidle" });
  await page.waitForTimeout(3000);
  const gs = page.getByRole("button", { name: "Get Started" });
  if (await gs.count()) { await gs.first().click(); }
  await page.waitForTimeout(4000);

  const search = page.getByPlaceholder(/Search city or address/);
  await search.fill("Mississauga");
  await page.waitForTimeout(3500);
  await page.locator("button", { hasText: /Mississauga/ }).first().click();
  await page.waitForTimeout(15000);

  const dir = "/tmp/claude-1000/-mnt-c-Users-minif-Downloads-UofT-Projects-hack-the-6IX/a44ecb3e-17eb-47ec-9f4f-d248d27a0516/scratchpad";
  await page.screenshot({ path: `${dir}/context-mississauga.png` });
  await browser.close();

  console.log("context fetches:", JSON.stringify(contextFetches));
  const away = contextFetches.filter(
    (f) => Math.abs(f.lat - 43.6532) > 0.02 || Math.abs(f.lng - -79.3832) > 0.02,
  );
  if (!away.length) throw new Error("no context fetch for the searched site");
  if (!away.some((f) => f.features > 0))
    throw new Error("searched-site context fetch returned zero buildings");
  console.log("PASS: context buildings follow the active site");
})().catch((e) => { console.error("FAIL:", e.message); process.exit(1); });
