const { test, expect } = require('@playwright/test');

test('Part 4.2 strategy lab shows working synthetic simulation, orders, fills, and charts', async ({page}) => {
  await page.goto('/strategy');
  await expect(page).toHaveTitle(/ATLAS/);
  await expect(page.getByTestId('source-badge')).toContainText('SYNTHETIC DEMO');
  await expect(page.getByTestId('final-equity')).toContainText('$');
  await expect(page.getByTestId('price-chart').locator('svg')).toBeVisible();
  await expect(page.getByTestId('fill-count')).not.toHaveText('—');
  await expect(page.getByRole('heading', {name:'Executed fills'})).toBeVisible();
  await expect(page.getByText('Orders & decisions', {exact:true})).toBeVisible();
});

test('saved data mode is visibly distinguishable from synthetic', async ({page}) => {
  await page.goto('/strategy');
  await page.getByTestId('data-mode').selectOption('saved');
  await expect(page.getByTestId('source-badge')).toContainText('saved Yahoo Finance');
  await expect(page.getByTestId('data-mode')).toHaveValue('saved');
});

test('invalid SMA lengths show an error and do not claim results', async ({page}) => {
  await page.goto('/strategy');
  await page.locator('#shortLen').fill('30');
  await page.locator('#longLen').fill('20');
  await page.getByRole('button',{name:'Run backtest'}).click();
  await expect(page.getByRole('alert')).toContainText('Short SMA must be shorter');
});
