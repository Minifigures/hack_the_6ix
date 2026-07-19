// Regression check: panning the map (no search) must refresh green plots and
// translucent context buildings for the new view.
const { chromium } = require("playwright");
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
  await page.addInitScript(() => sessionStorage.setItem("innsight-entered", "1"));

  const empties = [];
  const contexts = [];
  page.on("response", (res) => {
    const url = res.url();
    if (url.includes("/sites/empty")) {
      const u = new URL(url);
      empties.push({ lat: Number(u.searchParams.get("lat")), lng: Number(u.searchParams.get("lng")) });
    }
    if (url.includes("/sites/context")) {
      const u = new URL(url);
      contexts.push({ lat: Number(u.searchParams.get("lat")), lng: Number(u.searchParams.get("lng")) });
    }
  });

  await page.goto("http://localhost:3000/", { waitUntil: "networkidle" });
  await page.waitForTimeout(3000);
  const gs = page.getByRole("button", { name: "Get Started" });
  if (await gs.count()) { await gs.first().click(); }
  await page.waitForTimeout(9000);
  const beforeEmpty = empties.length;
  const beforeCtx = contexts.length;

  // Drag the canvas three times (~1 km total at demo zoom).
  for (let i = 0; i < 3; i++) {
    await page.mouse.move(640, 500);
    await page.mouse.down();
    await page.mouse.move(640, 140, { steps: 12 });
    await page.mouse.up();
    await page.waitForTimeout(1500);
  }
  await page.waitForTimeout(18000);

  const dir = "/tmp/claude-1000/-mnt-c-Users-minif-Downloads-UofT-Projects-hack-the-6IX/a44ecb3e-17eb-47ec-9f4f-d248d27a0516/scratchpad";
  await page.screenshot({ path: `${dir}/pan-follow.png` });
  await browser.close();

  console.log("empty fetches:", JSON.stringify(empties));
  console.log("context fetches:", JSON.stringify(contexts));
  if (empties.length <= beforeEmpty)
    throw new Error("panning did not refresh green plots (/sites/empty)");
  if (contexts.length <= beforeCtx)
    throw new Error("panning did not refresh context buildings (/sites/context)");
  const last = empties[empties.length - 1];
  const first = empties[0];
  const moved = Math.abs(last.lat - first.lat) + Math.abs(last.lng - first.lng);
  if (moved < 0.003) throw new Error("refresh happened but not for a new area");
  console.log("PASS: plots and context buildings follow the panned view");
})().catch((e) => { console.error("FAIL:", e.message); process.exit(1); });
