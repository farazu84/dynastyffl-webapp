// One-off diagnostic: load a page and report elements overflowing the viewport.
// Usage: node scripts/find-overflow.js [url]
const { chromium } = require('playwright');

const url = process.argv[2] || 'http://localhost:3000/archive';

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  await page.goto(url, { waitUntil: 'networkidle' });
  // give React a beat to render fetched data
  await page.waitForTimeout(1500);

  const result = await page.evaluate(() => {
    const vw = document.documentElement.clientWidth;
    const docScrollW = document.documentElement.scrollWidth;
    const named = (el) => {
      let path = el.tagName.toLowerCase();
      if (el.id) path += '#' + el.id;
      if (el.className && el.className.toString().trim())
        path += '.' + el.className.toString().trim().split(/\s+/).join('.');
      return path;
    };
    const offenders = [];
    document.querySelectorAll('*').forEach((el) => {
      const r = el.getBoundingClientRect();
      const cs = getComputedStyle(el);
      const mr = parseFloat(cs.marginRight) || 0;
      const ml = parseFloat(cs.marginLeft) || 0;
      // box past the edge, OR right margin extends the scroll area, OR
      // the element itself scrolls wider than it displays.
      const boxOver = r.right > vw + 1 || r.left < -1;
      const marginOver = r.right + mr > vw + 1;
      const selfScroll = el.scrollWidth - el.clientWidth > 1 && cs.overflowX !== 'auto' && cs.overflowX !== 'scroll';
      if (boxOver || marginOver || selfScroll) {
        offenders.push({
          path: named(el),
          left: Math.round(r.left),
          right: Math.round(r.right),
          width: Math.round(r.width),
          marginR: mr,
          marginL: ml,
          scrollW: el.scrollWidth,
          clientW: el.clientWidth,
          kids: el.children.length,
        });
      }
    });
    offenders.sort((a, b) => (b.right + b.marginR) - (a.right + a.marginR));
    return { vw, docScrollW, count: offenders.length, top: offenders.slice(0, 25) };
  });

  console.log(`URL: ${url}`);
  console.log(`viewport=${result.vw}  document.scrollWidth=${result.docScrollW}  overflow=${result.docScrollW - result.vw}px`);
  console.log(`offending elements: ${result.count}\n`);
  result.top.forEach((o) => {
    console.log(
      `right:${String(o.right).padStart(5)}  left:${String(o.left).padStart(5)}  w:${String(o.width).padStart(5)}` +
      `  mR:${o.marginR}  mL:${o.marginL}  scrollW:${o.scrollW}/clientW:${o.clientW}  kids:${o.kids}  ${o.path}`
    );
  });

  await browser.close();
})();
