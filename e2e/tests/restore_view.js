const util = require('../util');
it('restore_view"', async () => {
  await page.setViewport({width: 1500, height: 1000});
  await page.goto(
    'http://127.0.0.1:5001/#q={"dataset":"../test-data/pbmc3k_no_raw.h5ad","q":[{"id":"n_counts","type":"obs"},{"id":"ABCB1","type":"X"}]}',
  );
  await page.waitForSelector('[data-testid="scatter-chart-three"]');
  await page.evaluate(() => {
    document.querySelector('[data-testid="chart-extra"]').style.display =
      'none';
  });
  const element = await page.$('[data-testid="scatter-chart-three"] > canvas');
  await element.screenshot({path: 'restore_view.png'});

  util.diffImages('restore_view.png', 'tests/screenshots/restore_view.png', 0);
}, 10000);
