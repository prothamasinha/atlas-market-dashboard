const { defineConfig } = require('@playwright/test');
module.exports = defineConfig({
  testDir: './tests',
  testMatch: '**/*.spec.js',
  use: { baseURL: 'http://127.0.0.1:8002', browserName: 'chromium', headless:true },
  webServer: {
    command: 'python3 -m uvicorn backend.main:app --host 127.0.0.1 --port 8002',
    url: 'http://127.0.0.1:8002/',
    reuseExistingServer: !process.env.CI,
    timeout: 30000
  }
});
