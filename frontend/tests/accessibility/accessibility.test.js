const { toHaveNoViolations, axe } = require('jest-axe');
const { setupDomEnvironment } = require('../test_helper');

expect.extend(toHaveNoViolations);

describe('Accessibility Audit Tests', () => {
  let env;
  let window;
  let document;

  beforeEach(() => {
    env = setupDomEnvironment();
    window = env.window;
    document = env.document;
  });

  test('Authentication view is accessible', async () => {
    // Make sure we are on login view
    window.Auth.showLoginPage();
    const overlay = document.getElementById('authOverlay');

    const results = await axe(overlay);
    // Ignore rules that JSDOM or partial views lack (like page-level lang/title or frame attributes)
    // and concentrate on inputs, roles, labels, buttons
    expect(results).toHaveNoViolations();
  });

  test('Main Dashboard view is accessible', async () => {
    // Authenticate user
    const expTime = Math.floor(Date.now() / 1000) + 1000;
    const access = 'header.' + btoa(JSON.stringify({ username: 'salesexecutive', role: 'sales', exp: expTime })) + '.signature';
    window.localStorage.setItem('crm_accessToken', access);
    window.Auth.verifiedRole = 'sales';

    // Navigate to dashboard
    window.Router.navigate('dashboard');

    const pageRoot = document.getElementById('pageRoot');
    const results = await axe(pageRoot);
    expect(results).toHaveNoViolations();
  });

  test('Sales Enquiry Form is accessible with proper labels', async () => {
    // Authenticate user
    const expTime = Math.floor(Date.now() / 1000) + 1000;
    const access = 'header.' + btoa(JSON.stringify({ username: 'salesexecutive', role: 'sales', exp: expTime })) + '.signature';
    window.localStorage.setItem('crm_accessToken', access);
    window.Auth.verifiedRole = 'sales';

    // Navigate to form
    window.Router.navigate('enquiry-form');

    const form = document.getElementById('salesEnquiryForm');
    const results = await axe(form);
    expect(results).toHaveNoViolations();
  });
});
