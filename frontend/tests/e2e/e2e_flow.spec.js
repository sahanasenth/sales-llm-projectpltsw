import { test, expect } from '@playwright/test';
import fs from 'fs';
import path from 'path';

const screenshotDir = path.resolve(__dirname, '../../reports/screenshots');

test.beforeEach(async ({ page }) => {
  page.on('console', msg => console.log(`BROWSER CONSOLE: [${msg.type()}] ${msg.text()}`));
  page.on('pageerror', err => console.log(`BROWSER EXCEPTION: ${err.message}`));
});

test.describe('E2E Business Workflows & Visual Captures', () => {

  test.describe('Unauthenticated workflows', () => {
    // Override storageState to be empty
    test.use({ storageState: { cookies: [], origins: [] } });

    test('Login page loads and captures screenshot', async ({ page }) => {
      await page.goto('/');

      // Verify auth overlay is visible
      await expect(page.locator('#authOverlay')).toBeVisible();

      // Capture login page screenshot
      await page.screenshot({ path: path.join(screenshotDir, 'login_page.png') });

      // Perform login
      await page.fill('#authUsername', 'salesexecutive');
      await page.fill('#authPassword', 'sales123');
      await page.click('#loginBtn');

      // Verify dashboard loaded
      await expect(page.locator('#appShell')).toHaveClass(/auth-visible/);
    });
  });

  test.describe('Authenticated workflows', () => {
    test('Dashboard loads correctly and captures screenshot', async ({ page }) => {
      await page.goto('/');

      // Verify shell is authenticated and visible
      await expect(page.locator('#appShell')).toHaveClass(/auth-visible/);

      // Verify main components render (brand logo, sidebar navigation, topbar profile initials)
      await expect(page.locator('.brand-badge')).toContainText('SC');
      await expect(page.locator('#avatarBtn')).toContainText('admin', { ignoreCase: true });

      // Capture dashboard screenshot
      await page.screenshot({ path: path.join(screenshotDir, 'dashboard.png') });
    });

    test('Create enquiry form submit workflow', async ({ page }) => {
      await page.goto('/');

      // Navigate to Enquiry Form via sidebar link
      await page.click('[data-nav="enquiry-form"]');
      await expect(page.locator('.page-title h2')).toContainText('Enquiry Form');

      // Fill form fields
      const testName = `Automated E2E Test-${Date.now()}`;
      await page.fill('[name="customerName"]', testName);
      await page.selectOption('[name="enquirySource"]', 'Website');
      await page.fill('[name="phone"]', '9876543210');
      await page.fill('[name="modelName"]', 'R15');
      await page.fill('[name="email"]', 'e2e@test.com');
      await page.fill('[name="remarks"]', 'Automated QA pipeline check.');

      // Capture form screenshot before submitting
      await page.screenshot({ path: path.join(screenshotDir, 'enquiry_form.png') });

      // Submit form (specifically inside the sales enquiry form)
      await page.click('#salesEnquiryForm button[type="submit"]');

      // Should redirect to sales enquiries view
      await expect(page.locator('.page-title h2')).toContainText('Sales Enquiries');

      // The newly created enquiry should show in the records table
      const firstRowCustomer = page.locator('tbody tr:first-child td:nth-child(2)');
      await expect(firstRowCustomer).toContainText(testName);

      // Capture table view screenshot
      await page.screenshot({ path: path.join(screenshotDir, 'enquiries_table.png') });
    });

    test('Create appointment booking workflow', async ({ page }) => {
      await page.goto('/');

      // Navigate to Appointment Form
      await page.click('[data-nav="appointments"]');
      await page.click('button:has-text("Add Appointment")');
      await expect(page.locator('.page-title h2')).toContainText('New Appointment');

      // Fill form
      const apptName = `Appt-${Date.now()}`;
      await page.fill('[name="apptCustomer"]', apptName);
      await page.fill('[name="apptVehicle"]', 'Fascino');
      await page.fill('[name="apptDate"]', '2026-07-20');
      await page.fill('[name="apptTime"]', '14:30'); // 2:30 PM

      // Capture form screenshot
      await page.screenshot({ path: path.join(screenshotDir, 'appointment_form.png') });

      // Book (specifically inside the appointment form)
      await page.click('#appointmentForm button[type="submit"]');

      // Redirected back to appointments list
      await expect(page.locator('.page-title h2')).toContainText('Appointment Booking');

      // Verify newly scheduled appointment is listed
      const firstRowCustomer = page.locator('tbody tr:first-child td:nth-child(2)');
      await expect(firstRowCustomer).toContainText(apptName);

      // Capture appointments table screenshot
      await page.screenshot({ path: path.join(screenshotDir, 'appointments_table.png') });
    });

    test('Search and filter functionality', async ({ page }) => {
      await page.goto('/');
      await page.click('[data-nav="sales-enquiries"]');

      // Type search query
      await page.fill('#globalSearch', 'R15');
      await page.press('#globalSearch', 'Enter');

      // Verify filtered results
      // Capture filtered view screenshot
      await page.screenshot({ path: path.join(screenshotDir, 'search_filter_results.png') });
    });

    test('User logout flow resets authentication state', async ({ page }) => {
      await page.goto('/');

      // Click profile dropdown
      await page.click('#avatarBtn');

      // Click logout / sign out link
      await page.click('#logoutBtn');

      // Verify authentication overlay is shown again
      await expect(page.locator('#authOverlay')).not.toHaveClass(/hidden/);
      await expect(page.locator('#appShell')).not.toHaveClass(/auth-visible/);

      // Capture screen after logout
      await page.screenshot({ path: path.join(screenshotDir, 'logout_screen.png') });
    });
  });

  test.describe('Role restricted access workflows', () => {
    // Login as salesexecutive user
    test.use({ storageState: { cookies: [], origins: [] } });

    test('Access restricted routes redirects to Access Denied page', async ({ page }) => {
      await page.goto('/');

      // Login as salesexecutive
      await page.fill('#authUsername', 'salesexecutive');
      await page.fill('#authPassword', 'sales123');
      await page.click('#loginBtn');

      await expect(page.locator('#appShell')).toHaveClass(/auth-visible/);

      // Try to navigate directly to admin controls hash
      await page.evaluate(() => {
        window.location.hash = 'admin-controls';
      });

      // Verify that access denied view is shown
      await expect(page.locator('#pageRoot h2')).toContainText('403 Access Restricted');

      // Capture access denied screenshot
      await page.screenshot({ path: path.join(screenshotDir, 'access_denied.png') });
    });
  });

});
