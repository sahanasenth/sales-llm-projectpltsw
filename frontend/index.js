/* ═══════════════════════════════════════════════════════════════
   AUTH MODULE — Complete Frontend Authentication Workflow
═══════════════════════════════════════════════════════════════ */

/* ── Auth Token Keys ── */
var AUTH_KEYS = {
  ACCESS_TOKEN: "crm_accessToken",
  REFRESH_TOKEN: "crm_refreshToken",
  LOGGED_IN_USER: "crm_loggedInUser",
  TOKEN_EXPIRY: "crm_tokenExpiry",
  REMEMBER_ME: "crm_rememberMe",
  REMEMBERED_USER: "crm_rememberedUser",
};

/* ── Session-expiry notification flag (sessionStorage, cleared on browser close) ── */
var SESSION_EXPIRED_FLAG = "crm_sessionExpired";

/* ── Refresh lock: prevents concurrent refresh storms ── */
var _refreshing = null;

/* ═══════════════════════════════════════════════════════════════
 AUTH — Core Functions
═══════════════════════════════════════════════════════════════ */
var Auth = {
  verifiedRole: null,
  verifiedUser: null,

  /* ── Save tokens with expiry based on Remember Me ── */
  saveTokens(username, accessToken, refreshToken, rememberMe = false) {
    const decoded = this.parseJwt(accessToken);
    if (!decoded?.exp || !VALID_ROLES.includes(decoded.role)) {
      throw new Error("Invalid access token received from server");
    }
    const expiry = decoded.exp * 1000;

    localStorage.setItem(AUTH_KEYS.ACCESS_TOKEN, accessToken);
    localStorage.setItem(AUTH_KEYS.REFRESH_TOKEN, refreshToken);
    localStorage.setItem(AUTH_KEYS.LOGGED_IN_USER, username);
    localStorage.setItem(AUTH_KEYS.TOKEN_EXPIRY, String(expiry));
    this.verifiedRole = null;
    this.verifiedUser = null;
  },

  /* ── Save/load/clear Remember Me preferences ── */
  saveSession(username, rememberMe) {
    if (rememberMe) {
      localStorage.setItem(AUTH_KEYS.REMEMBER_ME, "true");
      localStorage.setItem(AUTH_KEYS.REMEMBERED_USER, username);
    } else {
      // Not remembered — clear any previous remembered state
      localStorage.removeItem(AUTH_KEYS.REMEMBER_ME);
      localStorage.removeItem(AUTH_KEYS.REMEMBERED_USER);
    }
  },

  loadRememberedUser() {
    const isRemembered =
      localStorage.getItem(AUTH_KEYS.REMEMBER_ME) === "true";
    if (isRemembered) {
      return localStorage.getItem(AUTH_KEYS.REMEMBERED_USER) || null;
    }
    return null;
  },

  clearRememberedSession() {
    localStorage.removeItem(AUTH_KEYS.REMEMBER_ME);
    localStorage.removeItem(AUTH_KEYS.REMEMBERED_USER);
  },

  /* ── Clear all auth tokens ── */
  clearTokens() {
    localStorage.removeItem(AUTH_KEYS.ACCESS_TOKEN);
    localStorage.removeItem(AUTH_KEYS.REFRESH_TOKEN);
    localStorage.removeItem(AUTH_KEYS.LOGGED_IN_USER);
    localStorage.removeItem(AUTH_KEYS.TOKEN_EXPIRY);
    this.verifiedRole = null;
    this.verifiedUser = null;
    // Note: REMEMBER_ME and REMEMBERED_USER are intentionally preserved
    // here so the username is still pre-filled after session expiry.
    // They are only cleared on explicit logoutUser() call.
  },

  /* ── Check if user is authenticated (token exists + not expired) ── */
  isAuthenticated() {
    const token = localStorage.getItem(AUTH_KEYS.ACCESS_TOKEN);
    if (!token) return false;
    const decoded = this.parseJwt(token);
    if (!decoded || !decoded.exp || !VALID_ROLES.includes(decoded.role)) {
      this.clearTokens();
      return false;
    }

    const expMs = decoded.exp * 1000;
    if (Date.now() > expMs) {
      sessionStorage.setItem(SESSION_EXPIRED_FLAG, "true");
      this.clearTokens();
      return false;
    }
    return true;
  },

  /* ── Get the currently logged-in username ── */
  getLoggedInUser() {
    return localStorage.getItem(AUTH_KEYS.LOGGED_IN_USER) || null;
  },

  /* ── Get the currently logged-in user role ── */
  getUserRole() {
    if (this.verifiedRole) return this.verifiedRole;
    // Always derive role from signed JWT to avoid trusting mutable localStorage values
    const token = this.getAccessToken();
    if (!token) return null;
    const decoded = this.parseJwt(token);
    if (!decoded) return null;
    // Respect token expiry embedded in JWT
    if (decoded.exp && Date.now() > decoded.exp * 1000) return null;
    return VALID_ROLES.includes(decoded.role) ? decoded.role : null;
  },

  /* ── Get access token (for use in API requests) ── */
  getAccessToken() {
    return localStorage.getItem(AUTH_KEYS.ACCESS_TOKEN) || null;
  },

  /* ── Validate login form fields ── */
  validateLoginForm(username, password) {
    const errors = [];
    if (!username || !username.trim()) {
      errors.push({
        field: "username",
        message: "Username or email is required.",
      });
    } else if (username.trim().length < 3) {
      errors.push({
        field: "username",
        message: "Username must be at least 3 characters.",
      });
    }
    if (!password || !password.trim()) {
      errors.push({
        field: "password",
        message: "Password is required.",
      });
    } else if (password.length < 6) {
      errors.push({
        field: "password",
        message: "Password must be at least 6 characters.",
      });
    }
    return { valid: errors.length === 0, errors };
  },

  /* ── Helper: Parse JWT without external libraries ── */
  parseJwt(token) {
    try {
      if (!token || token.split(".").length !== 3) return null;
      const base64Url = token.split(".")[1];
      if (!base64Url) return null;
      const base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/");
      const jsonPayload = decodeURIComponent(
        atob(base64)
          .split("")
          .map(function (c) {
            return "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2);
          })
          .join(""),
      );
      const decoded = JSON.parse(jsonPayload);
      if (decoded && decoded.role === "sales_executive") {
        decoded.role = "sales";
      }
      return decoded;
    } catch (e) {
      return null;
    }
  },

  requireValidSession() {
    if (!this.isAuthenticated() || !this.verifiedRole) {
      this.clearTokens();
      this._resetAppState();
      this.showLoginPage();
      return false;
    }
    return true;
  },

  verifySessionWithBackend() {
    return new Promise(async (resolve) => {
      if (!this.isAuthenticated()) return resolve(false);
      const token = this.getAccessToken();
      try {
        const response = await fetch("http://127.0.0.1:8000/api/auth/me/", {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
        });
        if (!response.ok) {
          this.clearTokens();
          return resolve(false);
        }
        const data = await response.json();
        if (data.role === "sales_executive") {
          data.role = "sales";
        }
        if (!VALID_ROLES.includes(data.role)) {
          this.clearTokens();
          return resolve(false);
        }
        const tokenRole = this.getUserRole();
        if (tokenRole && tokenRole !== data.role) {
          this.clearTokens();
          return resolve(false);
        }
        this.verifiedRole = data.role;
        this.verifiedUser = data.username;
        if (data.username) {
          localStorage.setItem(AUTH_KEYS.LOGGED_IN_USER, data.username);
        }
        resolve(true);
      } catch (err) {
        resolve(false);
      }
    });
  },

  /* ── Main loginUser function ── */
  async loginUser(username, password, rememberMe = false) {
    const response = await fetch("http://127.0.0.1:8000/api/token/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.detail || "Invalid credentials");
    }

    const data = await response.json();

    // Decode token to extract verified claims
    const decoded = this.parseJwt(data.access);
    const serverUsername = decoded?.username || username;

    this.saveTokens(
      serverUsername,
      data.access,
      data.refresh,
      rememberMe,
    );
    this.saveSession(serverUsername, rememberMe);
    const verified = await this.verifySessionWithBackend();
    if (!verified) {
      throw new Error("Unable to verify authenticated session");
    }
    return data;
  },

  /* ── Logout: clears all tokens, resets appState, returns to login ── */
  logoutUser() {
    this.clearTokens();
    this.clearRememberedSession();
    this._resetAppState();
    // Clear in-memory data store so stale data is never visible after re-login
    if (typeof Store !== "undefined") {
      Store.setEnquiries([]);
      Store.setAppointments([]);
      Store.setFeedback([]);
    }
    this.showLoginPage();
    Utils.toast("You have been signed out successfully.", "success");
  },

  /* ── FIX 4: Full appState reset on logout ── */
  _resetAppState() {
    appState.currentView = "dashboard";
    appState.sidebarCollapsed = false;
    appState.mobileSidebarOpen = false;
    appState.search = "";
    appState.filters = {
      enquiries: { status: "all", vehicle: "all", date: "all" },
      appointments: { status: "all", vehicle: "all", date: "all" },
      feedback: { status: "all", vehicle: "all", date: "all" },
    };
    appState.formDraft = {};
    // Clear persisted UI state so next login starts fresh
    try {
      localStorage.removeItem(LS_KEY + "_" + UI_STATE_STORAGE_KEY);
    } catch {}
  },

  /* ── authFetch: Authenticated API requests with automatic token refresh ── */
  async authFetch(url, options = {}, _isRetry = false) {
    if (!this.isAuthenticated() || !this.verifiedRole) {
      this.clearTokens();
      this._resetAppState();
      this.showLoginPage();
      throw new Error("Invalid or expired session.");
    }
    const token = this.getAccessToken();
    const headers = {
      "Content-Type": "application/json",
      ...(options.headers || {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    };

    const response = await fetch(url, { ...options, headers });

    if (response.status === 401 && !_isRetry) {
      // Attempt token refresh exactly once
      const refreshed = await this.refreshAccessToken();
      if (refreshed) {
        // Retry original request with new token
        return this.authFetch(url, options, true);
      }
      // Refresh failed — force logout with session expired notice
      sessionStorage.setItem(SESSION_EXPIRED_FLAG, "true");
      this.clearTokens();
      this._resetAppState();
      this.showLoginPage();
      this._checkSessionExpiry();
      throw new Error("Session expired. Please sign in again.");
    }

    return response;
  },

  /* ── Token Refresh: calls /api/token/refresh/ and updates access token ── */
  async refreshAccessToken() {
    // Deduplicate concurrent refresh calls — only one in-flight at a time
    if (_refreshing) return _refreshing;

    _refreshing = (async () => {
      try {
        const refreshToken = localStorage.getItem(
          AUTH_KEYS.REFRESH_TOKEN,
        );
        if (!refreshToken) return false;

        const response = await fetch(
          "http://127.0.0.1:8000/api/token/refresh/",
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ refresh: refreshToken }),
          },
        );

        if (!response.ok) return false;

        const data = await response.json();
        if (!data.access) return false;

        // Update stored access token and set expiry based on JWT exp claim when available
        localStorage.setItem(AUTH_KEYS.ACCESS_TOKEN, data.access);
        const decoded = this.parseJwt(data.access) || {};
        if (!decoded.exp || !VALID_ROLES.includes(decoded.role))
          return false;
        localStorage.setItem(
          AUTH_KEYS.TOKEN_EXPIRY,
          String(decoded.exp * 1000),
        );
        this.verifiedRole = decoded.role;

        return true;
      } catch {
        return false;
      } finally {
        _refreshing = null;
      }
    })();

    return _refreshing;
  },

  /* ── Show dashboard (called after successful login) ── */
  showDashboard() {
    const overlay = document.getElementById("authOverlay");
    const shell = document.getElementById("appShell");
    if (overlay) {
      overlay.style.opacity = "0";
      setTimeout(() => {
        overlay.style.display = "none";
        overlay.classList.add("hidden");
      }, 500);
    }
    if (shell) shell.classList.add("auth-visible");
  },

  /* ── Show login page (called on logout or unauthenticated access) ── */
  showLoginPage() {
    const overlay = document.getElementById("authOverlay");
    const shell = document.getElementById("appShell");
    if (overlay) {
      overlay.style.display = "flex";
      overlay.style.opacity = "1";
      overlay.classList.remove("hidden");
      // Reset form state
      const form = document.getElementById("loginForm");
      if (form) form.reset();
      const errBanner = document.getElementById("authErrorBanner");
      if (errBanner) errBanner.classList.remove("visible");
      // Re-populate remembered username if applicable
      this._restoreRememberedUser();
    }
    if (shell) shell.classList.remove("auth-visible");
  },

  /* ── Pre-fill remembered username on login page ── */
  _restoreRememberedUser() {
    const remembered = this.loadRememberedUser();
    const usernameEl = document.getElementById("authUsername");
    const rememberEl = document.getElementById("rememberMe");
    if (usernameEl && remembered) {
      usernameEl.value = remembered;
    }
    if (rememberEl && remembered) {
      rememberEl.checked = true;
    }
  },

  /* ── FIX 5: Show session expiry notification if flag is set ── */
  _checkSessionExpiry() {
    const wasExpired = sessionStorage.getItem(SESSION_EXPIRED_FLAG);
    if (wasExpired) {
      sessionStorage.removeItem(SESSION_EXPIRED_FLAG);
      // Delay slightly so the login page renders first
      setTimeout(() => {
        const errBanner = document.getElementById("authErrorBanner");
        const errText = document.getElementById("authErrorText");
        if (errBanner && errText) {
          errText.textContent =
            "Your session has expired. Please sign in again.";
          errBanner.classList.add("visible");
        }
        // Also fire an amber-styled toast for clear UX feedback
        Utils.toast("Session expired — please sign in again.", "warning");
      }, 300);
    }
  },

  /* ── Initialize authentication on page load ── */
  initializeAuth() {
    return new Promise(async (resolve) => {
      if (
        this.isAuthenticated() &&
        (await this.verifySessionWithBackend())
      ) {
        const role = this.getUserRole();

        const hash = window.location.hash.replace("#", "");
        const defaultRoute = DEFAULT_ROUTE_BY_ROLE[role] || "dashboard";
        const requestedView =
          hash || appState.currentView || defaultRoute;
        Router.navigate(
          resolveNavigationTarget(requestedView, role).viewId,
        );
        this.showDashboard();
        resolve();
      } else {
        this.clearTokens();
        this.showLoginPage();
        this._checkSessionExpiry();
        resolve();
      }
      this._bindLoginForm();
    });
  },

  /* ── Bind login form events ── */
  _bindLoginForm() {
    const form = document.getElementById("loginForm");
    const loginBtn = document.getElementById("loginBtn");
    const pwToggle = document.getElementById("pwToggle");
    const pwInput = document.getElementById("authPassword");
    const errBanner = document.getElementById("authErrorBanner");
    const errText = document.getElementById("authErrorText");

    if (!form) return;

    // Password visibility toggle
    if (pwToggle && pwInput) {
      pwToggle.addEventListener("click", () => {
        const isHidden = pwInput.type === "password";
        pwInput.type = isHidden ? "text" : "password";
        pwToggle.textContent = isHidden ? "🙈" : "👁";
      });
    }

    // Clear error styling on input
    ["authUsername", "authPassword"].forEach((id) => {
      const el = document.getElementById(id);
      if (el) {
        el.addEventListener("input", () => {
          el.classList.remove("auth-error");
          if (errBanner) errBanner.classList.remove("visible");
        });
      }
    });

    // Form submit
    form.addEventListener("submit", async (e) => {
      e.preventDefault();

      const usernameEl = document.getElementById("authUsername");
      const passwordEl = document.getElementById("authPassword");
      const rememberEl = document.getElementById("rememberMe");
      const username = usernameEl?.value || "";
      const password = passwordEl?.value || "";
      const rememberMe = rememberEl?.checked || false;

      // Frontend validation
      const validation = Auth.validateLoginForm(username, password);
      if (!validation.valid) {
        validation.errors.forEach((err) => {
          const fieldEl = document.getElementById(
            err.field === "username" ? "authUsername" : "authPassword",
          );
          if (fieldEl) fieldEl.classList.add("auth-error");
        });
        if (errBanner && errText) {
          errText.textContent = validation.errors[0].message;
          errBanner.classList.add("visible");
        }
        return;
      }

      // Loading state
      if (loginBtn) {
        loginBtn.disabled = true;
        loginBtn.innerHTML = '<span class="auth-spinner"></span>';
      }

      try {
        await Auth.loginUser(username, password, rememberMe);

        // Load backend data now that the user is authenticated
        await Actions.refreshAll();

        // Success — resolve the route before revealing the shell
        const role = Auth.getUserRole();

        if (role === "director") {
          Utils.toast(
            "Welcome, Director. Accessing Strategic Panel...",
            "success",
          );
          Router.navigate(DEFAULT_ROUTE_BY_ROLE.director);
        } else if (role === "admin") {
          Router.navigate(DEFAULT_ROUTE_BY_ROLE.admin);
          Utils.toast("Welcome, Admin. Accessing controls.", "success");
        } else {
          Router.navigate(DEFAULT_ROUTE_BY_ROLE[role] || "dashboard");
          Utils.toast(
            `Welcome back, ${Auth.getLoggedInUser()}! 🎉`,
            "success",
          );
        }

        Auth.showDashboard();

        // Re-render topbar to show logged-in user info
        Renderer.topbar();
      } catch (err) {
        // Failed login — highlight fields and show error
        if (usernameEl) usernameEl.classList.add("auth-error");
        if (passwordEl) passwordEl.classList.add("auth-error");
        if (errBanner && errText) {
          errText.textContent =
            "Invalid username or password. Please try again.";
          errBanner.classList.add("visible");
        }
      } finally {
        if (loginBtn) {
          loginBtn.disabled = false;
          loginBtn.innerHTML = '<span id="loginBtnText">Sign In</span>';
        }
      }
    });
  },
};

/* ─────────────────────────────────────────────────────────────
 END OF AUTH MODULE
───────────────────────────────────────────────────────────── */

var API_BASE = "http://127.0.0.1:8000/api";

var getApiErrorMessage = async (response, fallbackMessage) => {
  const data = await response.json().catch(() => ({}));
  if (response.status === 403) {
    return "Access denied. You don't have permission to access this resource.";
  }
  return data.detail || fallbackMessage;
};

var Api = {
  async getEnquiries() {
    const response = await Auth.authFetch(`${API_BASE}/enquiry/`);
    if (!response.ok) {
      throw new Error(
        await getApiErrorMessage(response, "Failed to fetch enquiries"),
      );
    }
    return response.json();
  },

  async createEnquiry(payload) {
    const response = await Auth.authFetch(`${API_BASE}/enquiry/create/`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      throw new Error(
        await getApiErrorMessage(response, "Failed to save enquiry."),
      );
    }
    const data = await response.json();
    return data;
  },

  async getAppointments() {
    const response = await Auth.authFetch(`${API_BASE}/appointment/`);
    if (!response.ok) {
      throw new Error(
        await getApiErrorMessage(
          response,
          "Failed to fetch appointments",
        ),
      );
    }
    return response.json();
  },

  async createAppointment(payload) {
    const response = await Auth.authFetch(
      `${API_BASE}/appointment/create/`,
      {
        method: "POST",
        body: JSON.stringify(payload),
      },
    );
    if (!response.ok) {
      throw new Error(
        await getApiErrorMessage(
          response,
          "Failed to save appointment.",
        ),
      );
    }
    const data = await response.json();
    return data;
  },

  async getFeedback() {
    const response = await Auth.authFetch(`${API_BASE}/feedback/`);
    if (!response.ok) {
      throw new Error(
        await getApiErrorMessage(response, "Failed to fetch feedback"),
      );
    }
    return response.json();
  },

  async createFeedback(payload) {
    const response = await Auth.authFetch(
      `${API_BASE}/feedback/create/`,
      {
        method: "POST",
        body: JSON.stringify(payload),
      },
    );
    if (!response.ok) {
      throw new Error(
        await getApiErrorMessage(response, "Failed to save feedback."),
      );
    }
    const data = await response.json();
    return data;
  },

  async getDirectorReport() {
    const response = await Auth.authFetch(
      `${API_BASE}/director/revenue/`,
    );
    if (!response.ok) throw new Error("Failed to fetch director report");
    return response.json();
  },

  async getAdminLogs() {
    const response = await Auth.authFetch(`${API_BASE}/admin/logs/`);
    if (!response.ok) throw new Error("Failed to fetch audit logs");
    return response.json();
  },
};

/* ═══════════════════════════════════════════════════════════════
 STATE
═══════════════════════════════════════════════════════════════ */
var appState = {
  currentView: "dashboard",
  sidebarCollapsed: false,
  mobileSidebarOpen: false,
  search: "",
  filters: {
    enquiries: { status: "all", vehicle: "all", date: "all" },
    appointments: { status: "all", vehicle: "all", date: "all" },
    feedback: { status: "all", vehicle: "all", date: "all" },
  },
  formDraft: {},
};

var UI_STATE_STORAGE_KEY = "uiState";

/* ═══════════════════════════════════════════════════════════════
 DATA STORE
═══════════════════════════════════════════════════════════════ */

/* ── localStorage helpers ── */
var LS_KEY = "salesCRM_modular";
var _load = (key) => {
  try {
    const v = localStorage.getItem(LS_KEY + "_" + key);
    return v ? JSON.parse(v) : null;
  } catch {
    return null;
  }
};
var _save = (key, data) => {
  try {
    localStorage.setItem(LS_KEY + "_" + key, JSON.stringify(data));
  } catch {
    /* storage full — fail silently */
  }
};

var Persist = {
  saveUI() {
    _save(UI_STATE_STORAGE_KEY, {
      currentView: appState.currentView,
      sidebarCollapsed: appState.sidebarCollapsed,
      search: appState.search,
      filters: appState.filters,
    });
  },
  loadUI() {
    const saved = _load(UI_STATE_STORAGE_KEY);
    if (!saved || typeof saved !== "object") return;

    if (
      typeof saved.currentView === "string" &&
      saved.currentView in Views
    ) {
      appState.currentView = saved.currentView;
    }
    if (typeof saved.sidebarCollapsed === "boolean") {
      appState.sidebarCollapsed = saved.sidebarCollapsed;
    }
    if (typeof saved.search === "string") {
      appState.search = saved.search;
    }
    if (saved.filters && typeof saved.filters === "object") {
      Object.keys(appState.filters).forEach((key) => {
        const src = saved.filters[key];
        if (!src || typeof src !== "object") return;
        appState.filters[key] = {
          status: typeof src.status === "string" ? src.status : "all",
          vehicle: typeof src.vehicle === "string" ? src.vehicle : "all",
          date: typeof src.date === "string" ? src.date : "all",
        };
      });
    }
  },
};

/* ── Central Store: all data from API ── */
var Store = {
  enquiries: [],
  appointments: [],
  feedback: [],
  directorReport: null,
  adminLogs: [],

  setEnquiries(records) {
    this.enquiries = records;
  },

  addEnquiry(record) {
    this.enquiries.unshift(record);
  },

  setAppointments(records) {
    this.appointments = records;
  },

  addAppointment(record) {
    this.appointments.unshift(record);
  },

  setFeedback(records) {
    this.feedback = records;
  },

  addFeedback(record) {
    this.feedback.unshift(record);
  },

  setDirectorReport(data) {
    this.directorReport = data;
  },

  setAdminLogs(logs) {
    this.adminLogs = logs;
  },
};

var Actions = {
  async refreshAll() {
    const role = Auth.getUserRole();
    if (!Auth.requireValidSession()) return;
    try {
      const canReadEnquiries = role === "admin" || role === "director";
      const canReadAppointments =
        role === "admin" ||
        role === "director" ||
        role === "salesmanager" ||
        role === "manager";
      const canReadFeedback = role === "admin" || role === "director";

      if (canReadEnquiries || canReadAppointments || canReadFeedback) {
        const [enq, app, fdb] = await Promise.all([
          canReadEnquiries ? Api.getEnquiries() : Promise.resolve([]),
          canReadAppointments ? Api.getAppointments() : Promise.resolve([]),
          canReadFeedback ? Api.getFeedback() : Promise.resolve([]),
        ]);

        // Map backend fields to frontend local fields for consistency
        Store.setEnquiries(
          enq.map((item) => ({
            id: item.enquiry_id,
            customer: item.customer,
            vehicle: item.vehicle,
            temperature: item.temperature,
            status: item.status,
            date: item.date,
            source: item.source,
          })),
        );

        Store.setAppointments(
          app.map((item) => ({
            id: item.appointment_id,
            customer: item.customer,
            vehicle: item.vehicle,
            status: item.status,
            date: item.date,
            time: item.time,
          })),
        );

        Store.setFeedback(
          fdb.map((item) => ({
            id: item.feedback_id,
            enquiryId: item.enquiry_id,
            customer: item.customer,
            vehicle: item.vehicle,
            status: item.status,
            date: item.date,
            rating: item.rating,
            feedback_text: item.feedback_text,
          })),
        );
      } else {
        Store.setEnquiries([]);
        Store.setAppointments([]);
        Store.setFeedback([]);
      }

      if (role === "admin" || role === "director") {
        const report = await Api.getDirectorReport();
        Store.setDirectorReport(report);
      } else {
        Store.setDirectorReport(null);
      }

      if (role === "admin") {
        const logs = await Api.getAdminLogs();
        Store.setAdminLogs(logs);
      } else {
        Store.setAdminLogs([]);
      }
    } catch (e) {
      console.error("Data refresh failed", e);
      Utils.toast(
        "Database sync failed. Working with cached data.",
        "warning",
      );
    }
  },
};

/* ═══════════════════════════════════════════════════════════════
 CONFIG: NAVIGATION
═══════════════════════════════════════════════════════════════ */
var ROUTE_CONFIG = [
  {
    id: "dashboard",
    label: "Dashboard",
    icon: "⌂",
    group: "Workspace",
    roles: ["admin", "director", "salesmanager", "sales"],
    nav: true,
  },
  {
    id: "sales-enquiries",
    label: "Sales Enquiries",
    icon: "▣",
    group: "Sales",
    roles: ["admin", "salesmanager", "sales"],
    nav: true,
  },
  {
    id: "enquiry-form",
    label: "Enquiry Form",
    icon: "✎",
    group: "Sales",
    roles: ["admin", "salesmanager", "sales"],
    nav: true,
  },
  {
    id: "appointments",
    label: "Appointment Booking",
    icon: "🗓",
    group: "Sales",
    roles: ["admin", "salesmanager", "sales"],
    nav: true,
  },
  {
    id: "appointment-form",
    label: "New Appointment",
    group: "Sales",
    roles: ["admin", "salesmanager", "sales"],
    nav: false,
  },
  {
    id: "feedback",
    label: "Sales Feedback",
    icon: "☰",
    group: "Sales",
    roles: ["admin", "salesmanager", "sales"],
    nav: true,
  },
  {
    id: "reports",
    label: "Executive Reports",
    icon: "📊",
    group: "Director",
    roles: ["admin", "director"],
    nav: true,
  },
  {
    id: "director-dashboard",
    label: "Director Panel",
    icon: "📈",
    group: "Director",
    roles: ["admin", "director"],
    nav: true,
  },
  {
    id: "admin-controls",
    label: "Admin Settings",
    icon: "⚙",
    group: "System",
    roles: ["admin"],
    nav: true,
  },
];

var NAV_CONFIG = ROUTE_CONFIG.filter((route) => route.nav);
var DEFAULT_ROUTE_BY_ROLE = {
  admin: "admin-controls",
  director: "director-dashboard",
  salesmanager: "dashboard",
  sales: "dashboard",
};
var VALID_ROLES = Object.keys(DEFAULT_ROUTE_BY_ROLE);
var ROUTE_REDIRECTS_BY_ROLE = {
  admin: {
    dashboard: "admin-controls",
  },
  director: {
    dashboard: "director-dashboard",
  },
};

function resolveRouteForRole(viewId, role) {
  return ROUTE_REDIRECTS_BY_ROLE[role]?.[viewId] || viewId;
}

function resolveNavigationTarget(viewId, role) {
  const resolvedViewId = resolveRouteForRole(viewId, role);
  let navItem = ROUTE_CONFIG.find((item) => item.id === resolvedViewId);

  // Allow loose matching (e.g. 'admin' matches 'admin-controls')
  if (!navItem) {
    navItem = ROUTE_CONFIG.find((item) =>
      item.id.startsWith(resolvedViewId),
    );
  }

  if (!navItem) {
    return {
      viewId: resolvedViewId,
      navItem: null,
      allowed: false,
      deniedRoute: resolvedViewId || "Unknown route",
    };
  }

  return {
    viewId: navItem.id,
    navItem,
    allowed: !navItem.roles || navItem.roles.includes(role),
    deniedRoute: navItem.label,
  };
}

/* ═══════════════════════════════════════════════════════════════
 CONFIG: ENQUIRY FORM FIELDS
═══════════════════════════════════════════════════════════════ */
var ENQUIRY_FORM_FIELDS = [
  { section: "Customer & Enquiry Details" },
  { label: "Date", name: "date", type: "date" },
  {
    label: "Customer Name",
    name: "customerName",
    type: "text",
    placeholder: "Enter customer name",
    required: true,
  },
  {
    label: "Enquiry Type",
    name: "enquiryType",
    type: "select",
    options: ["Direct", "Test Ride", "Website Lead", "Showroom Visit"],
  },
  {
    label: "Customer Enquiry Date",
    name: "customerEnquiryDate",
    type: "date",
  },
  {
    label: "Customer Type",
    name: "customerType",
    type: "select",
    options: [
      "New Customer",
      "Existing Customer",
      "Corporate",
      "Referral",
    ],
  },
  {
    label: "Test Ride Taken",
    name: "testRide",
    type: "select",
    options: ["Yes", "No"],
  },
  {
    label: "Enquiry Source",
    name: "enquirySource",
    type: "select",
    options: ["Walk-in", "Phone Call", "Website", "Referral"],
  },
  {
    label: "Gender",
    name: "gender",
    type: "select",
    options: ["Male", "Female", "Other"],
  },
  {
    label: "Payment Type",
    name: "paymentType",
    type: "select",
    options: ["Cash", "Finance", "EMI", "Undecided"],
    conditionalTarget: "financeDetails",
  },
  {
    label: "Sales Enquiry Status",
    name: "salesEnquiryStatus",
    type: "select",
    options: ["Submitted", "Draft", "Closed"],
  },
  {
    label: "Lead Temperature",
    name: "leadTemperature",
    type: "chips",
    options: ["Hot", "Warm", "Cold"],
    hint: "Prioritize follow-up urgency.",
  },
  {
    label: "Phone Number",
    name: "phone",
    type: "tel",
    placeholder: "10 digit mobile number",
    required: true,
  },
  {
    label: "Model Code",
    name: "modelCode",
    type: "text",
    placeholder: "Example: FA-220",
  },
  {
    label: "WhatsApp Number",
    name: "whatsapp",
    type: "tel",
    placeholder: "WhatsApp number",
  },
  {
    label: "Model Name",
    name: "modelName",
    type: "text",
    placeholder: "Selected bike model",
    required: true,
  },
  { label: "Follow Up Date", name: "followUpDate", type: "date" },
  {
    label: "Email Address",
    name: "email",
    type: "email",
    placeholder: "name@example.com",
  },
  {
    label: "Source of Information",
    name: "sourceInfo",
    type: "select",
    options: ["Newspaper", "Instagram", "Friend", "Dealer Board"],
  },
  {
    label: "Customer Interested in Exchange",
    name: "exchange",
    type: "select",
    options: ["Yes", "No", "Maybe"],
    conditionalTarget: "exchangeDetails",
  },
  {
    label: "Remarks",
    name: "remarks",
    type: "textarea",
    placeholder: "Add notes about customer intent",
    full: true,
  },

  { section: "Address Details" },
  {
  label: "Address 1",
  name: "address1",
  type: "text",
  placeholder: "Primary address",
  },
  {
    label: "Address 4",
    name: "address4",
    type: "text",
    placeholder: "Landmark / extra details",
  },
  {
    label: "Address 2",
    name: "address2",
    type: "text",
    placeholder: "Secondary address",
  },
  {
    label: "District",
    name: "district",
    type: "text",
    placeholder: "District",
  },
  {
    label: "Address 3",
    name: "address3",
    type: "text",
    placeholder: "Area / locality",
  },
  { label: "City", name: "city", type: "text", placeholder: "City" },
  {
    label: "Pincode",
    name: "pincode",
    type: "text",
    placeholder: "Pincode",
  },
  { label: "State", name: "state", type: "text", placeholder: "State" },
];

/* ═══════════════════════════════════════════════════════════════
 CONFIG: TABLE DEFINITIONS
═══════════════════════════════════════════════════════════════ */
var TABLE_CONFIG = {
  enquiries: {
    title: "Enquiry Records",
    subtitle: "Reusable table with status, vehicle, and date filters.",
    tableKey: "enquiries",
    searchKeys: [
      "id",
      "customer",
      "vehicle",
      "source",
      "status",
      "temperature",
    ],
    addLabel: "Open Form",
    addView: "enquiry-form",
    columns: [
      { key: "id", label: "ID" },
      { key: "customer", label: "Customer Name" },
      { key: "vehicle", label: "Vehicle Model" },
      { key: "temperature", label: "Lead Temp", type: "badge" },
      { key: "status", label: "Status", type: "badge" },
      { key: "date", label: "Date" },
      { key: "source", label: "Source" },
    ],
  },
  appointments: {
    title: "Appointment Schedule",
    subtitle: "Reusable appointment table with the same layout system.",
    tableKey: "appointments",
    searchKeys: ["id", "customer", "vehicle", "status", "date"],
    addLabel: "New Appointment",
    addView: "appointment-form",
    columns: [
      { key: "id", label: "Appointment ID" },
      { key: "customer", label: "Customer Name" },
      { key: "vehicle", label: "Vehicle" },
      { key: "status", label: "Status", type: "badge" },
      { key: "date", label: "Date" },
      { key: "time", label: "Time" },
    ],
  },
  feedback: {
    title: "Feedback Records",
    subtitle:
      "Reusable feedback table with consistent filtering and status display.",
    tableKey: "feedback",
    searchKeys: ["id", "enquiryId", "customer", "vehicle", "status"],
    columns: [
      { key: "id", label: "Feedback ID" },
      { key: "enquiryId", label: "Enquiry ID" },
      { key: "customer", label: "Customer" },
      { key: "vehicle", label: "Vehicle" },
      { key: "status", label: "Status", type: "badge" },
      { key: "date", label: "Date" },
    ],
  },
};

/* ═══════════════════════════════════════════════════════════════
 UTILITIES
═══════════════════════════════════════════════════════════════ */
var Utils = {
  escape(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  },
  capitalize(value) {
    return String(value).charAt(0).toUpperCase() + String(value).slice(1);
  },
  badgeClass(status) {
    const key = String(status).toLowerCase();
    const map = {
      submitted: "submitted",
      closed: "closed",
      completed: "completed",
      scheduled: "scheduled",
      pending: "pending",
      hot: "hot",
      warm: "warm",
      cold: "cold",
    };
    return map[key] || "draft";
  },
  uniqueValues(rows, key) {
    return [...new Set(rows.map((r) => r[key]).filter(Boolean))];
  },
  filterRows(rows, config, searchKeys) {
    const q = appState.search.trim().toLowerCase();
    return rows.filter((row) => {
      const searchMatch =
        !q ||
        searchKeys.some((key) =>
          String(row[key] || "")
            .toLowerCase()
            .includes(q),
        );
      const statusMatch =
        config.status === "all" ||
        String(row.status || "").toLowerCase() === config.status;
      const vehicleMatch =
        config.vehicle === "all" ||
        String(row.vehicle || "").toLowerCase() === config.vehicle;
      const dateMatch =
        config.date === "all" ||
        String(row.date || "").startsWith(config.date);
      return searchMatch && statusMatch && vehicleMatch && dateMatch;
    });
  },
  toast(message, type = "success") {
    const container = document.getElementById("toastContainer");
    const el = document.createElement("div");
    el.className = `toast ${type}`;
    const icons = { success: "✓", error: "✕", warning: "⚠" };
    const icon = icons[type] || "✓";
    el.innerHTML = `<span>${icon}</span> ${Utils.escape(message)}`;
    container.appendChild(el);
    setTimeout(() => {
      el.style.opacity = "0";
      el.style.transition = "opacity 0.3s";
      setTimeout(() => el.remove(), 300);
    }, 3200);
  },
  computeMetrics() {
    const rows = Store.enquiries;
    const submitted = rows.filter((r) => r.status === "Submitted").length;
    const draft = rows.filter((r) => r.status === "Draft").length;
    const closed = rows.filter((r) => r.status === "Closed").length;
    return [
      {
        label: "Total Enquiries",
        value: rows.length,
        icon: "◎",
        trend: "-",
      },
      {
        label: "Open Pipeline",
        value: submitted + draft,
        icon: "◔",
        trend: "-",
      },
      {
        label: "Appointments",
        value: Store.appointments.length,
        icon: "◫",
        trend: "-",
      },
      {
        label: "Closed Leads",
        value: closed,
        icon: "✓",
        trend: "-",
      },
    ];
  },
};

/* ═══════════════════════════════════════════════════════════════
 COMPONENTS
═══════════════════════════════════════════════════════════════ */
var Components = {
  /* ── Sidebar ── */
  sidebar() {
    const userRole = Auth.getUserRole();
    if (!userRole) return "";

    // Filter NAV_CONFIG based on role
    const filteredNav = NAV_CONFIG.filter(
      (item) => !item.roles || item.roles.includes(userRole),
    );

    const groups = [...new Set(filteredNav.map((item) => item.group))];
    const groupHTML = groups
      .map((group) => {
        const items = filteredNav
          .filter((item) => item.group === group)
          .map(
            (item) => `
      <div class="nav-link ${appState.currentView === item.id ? "active" : ""}"
           data-nav="${Utils.escape(item.id)}" role="button" tabindex="0">
        <span class="nav-icon">${item.icon}</span>
        <span class="nav-text">${Utils.escape(item.label)}</span>
      </div>
    `,
          )
          .join("");
        return `
      <div>
        <div class="nav-group-title">${Utils.escape(group)}</div>
        <div class="nav-menu">${items}</div>
      </div>
    `;
      })
      .join("");

    return `
    <div class="brand">
      <div class="brand-badge">SC</div>
      <div class="brand-copy">
        <h1>Sales Command</h1>
        <p>Professional CRM Workspace</p>
      </div>
    </div>
    ${groupHTML}
    <div class="sidebar-footer">
      <h3>Module Scope</h3>
      <p>Enquiries · Appointments · Feedback · Modular architecture</p>
    </div>
  `;
  },

  /* ── Topbar ── */
  topbar() {
    const user = Auth.getLoggedInUser();
    const initials = user
      ? user.split("@")[0].slice(0, 2).toUpperCase()
      : "SC";
    const displayName = user || "Sales Executive";

    return `
    <div class="topbar-left">
      <button class="icon-btn" id="sidebarToggle" aria-label="Toggle sidebar">☰</button>
      <div class="search-box">
        <span>⌕</span>
        <input id="globalSearch" type="text"
          placeholder="Search customers, vehicles, or records"
          value="${Utils.escape(appState.search)}" />
      </div>
    </div>
    <div class="topbar-right">
      <span class="auth-session-badge" title="Session active">
        <span class="auth-session-dot"></span>
        Secured
      </span>
      <button class="icon-btn" title="Notifications">🔔</button>
      <button class="icon-btn" title="Help">?</button>
      <div style="position:relative;">
        <button class="avatar-btn" id="avatarBtn" aria-haspopup="true" aria-expanded="false">
          <div class="avatar">${initials}</div>
          <div class="avatar-copy">
            <strong>${Utils.escape(displayName)}</strong>
            <span>CRM Workspace</span>
          </div>
        </button>
        <div class="profile-menu" id="profileMenu" role="menu">
          <div class="profile-item" role="menuitem">👤 Profile</div>
          <div class="profile-item" role="menuitem">⚙ Settings</div>
          <div class="profile-item logout-item" id="logoutBtn" role="menuitem">⇥ Sign out</div>
        </div>
      </div>
    </div>
  `;
  },

  /* ── Card ── */
  card({ title, subtitle, content, actionLabel, actionView }) {
    return `
    <section class="card">
      <div class="card-header">
        <div>
          <h3>${Utils.escape(title)}</h3>
          ${subtitle ? `<p>${Utils.escape(subtitle)}</p>` : ""}
        </div>
        ${
          actionLabel
            ? `<button class="btn btn-secondary" data-nav="${Utils.escape(actionView || "")}">${Utils.escape(actionLabel)}</button>`
            : ""
        }
      </div>
      <div class="card-body">${content}</div>
    </section>
  `;
  },

  /* ── Stat Cards ── */
  statCards() {
    return `
    <div class="stats-grid">
      ${Utils.computeMetrics()
        .map(
          (item) => `
        <section class="card stat-card">
          <div class="stat-top">
            <div>
              <small>${Utils.escape(item.label)}</small>
              <h3>${item.value}</h3>
            </div>
            <div class="stat-icon">${item.icon}</div>
          </div>
          <div class="trend">${Utils.escape(item.trend)}</div>
        </section>
      `,
        )
        .join("")}
    </div>
  `;
  },

  /* ── Table ── */
  table(cfg, rows) {
    const {
      title,
      subtitle,
      tableKey,
      columns,
      searchKeys,
      addLabel,
      addView,
    } = cfg;
    const config = appState.filters[tableKey];
    const filtered = Utils.filterRows(rows, config, searchKeys);
    const vehicleOpts = Utils.uniqueValues(rows, "vehicle");
    const monthOpts = [
      ...new Set(rows.map((r) => String(r.date).slice(0, 7))),
    ];

    const statusOptions = [
      ...new Set(rows.map((r) => String(r.status).toLowerCase())),
    ];

    const toolbar = `
    <div class="table-toolbar">
      <div class="toolbar-left">
        <select class="control" data-filter="${tableKey}" data-filter-key="status">
          <option value="all" ${config.status === "all" ? "selected" : ""}>All Status</option>
          ${statusOptions
            .map(
              (s) =>
                `<option value="${s}" ${config.status === s ? "selected" : ""}>${Utils.capitalize(s)}</option>`,
            )
            .join("")}
        </select>
        <select class="control" data-filter="${tableKey}" data-filter-key="vehicle">
          <option value="all" ${config.vehicle === "all" ? "selected" : ""}>All Vehicles</option>
          ${vehicleOpts
            .map(
              (v) =>
                `<option value="${v.toLowerCase()}" ${config.vehicle === v.toLowerCase() ? "selected" : ""}>${Utils.escape(v)}</option>`,
            )
            .join("")}
        </select>
        <select class="control" data-filter="${tableKey}" data-filter-key="date">
          <option value="all" ${config.date === "all" ? "selected" : ""}>All Dates</option>
          ${monthOpts
            .map(
              (m) =>
                `<option value="${m}" ${config.date === m ? "selected" : ""}>${m}</option>`,
            )
            .join("")}
        </select>
      </div>
      <div class="toolbar-right">
        ${
          addLabel
            ? `<button class="btn btn-primary" data-nav="${Utils.escape(addView || "")}">${Utils.escape(addLabel)}</button>`
            : ""
        }
      </div>
    </div>
  `;

    const tableRows = filtered.length
      ? filtered
          .map(
            (row) => `
        <tr>
          ${columns
            .map((col) => {
              if (col.type === "badge") {
                const val = row[col.key] || "";
                return `<td><span class="badge ${Utils.badgeClass(val)}">${Utils.escape(val)}</span></td>`;
              }
              return `<td>${Utils.escape(String(row[col.key] ?? "—"))}</td>`;
            })
            .join("")}
        </tr>
      `,
          )
          .join("")
      : `<tr><td colspan="${columns.length}" class="empty-state">No matching records found for the current filters.</td></tr>`;

    const content = `
    ${toolbar}
    <div class="table-wrap">
      <table>
        <thead>
          <tr>${columns.map((col) => `<th>${Utils.escape(col.label)}</th>`).join("")}</tr>
        </thead>
        <tbody>${tableRows}</tbody>
      </table>
    </div>
  `;

    return Components.card({ title, subtitle, content });
  },

  /* ── Form Field ── */
  formField(field) {
    if (field.section) {
      return `<div class="form-section"><h4>${Utils.escape(field.section)}</h4></div>`;
    }

    const cls = field.full ? "field full" : "field";
    const req = field.required ? 'data-required="true"' : "";
    const errMsg = field.required
      ? '<span class="error-msg">This field is required.</span>'
      : "";

    if (field.type === "select") {
      const cond = field.conditionalTarget
        ? `data-conditional="${field.conditionalTarget}"`
        : "";
      return `
      <div class="${cls}">
        <label>${Utils.escape(field.label)}</label>
        <select name="${field.name}" ${cond} ${req}>
          <option value="">Select ${Utils.escape(field.label)}</option>
          ${field.options
            .map(
              (o) =>
                `<option value="${Utils.escape(o)}">${Utils.escape(o)}</option>`,
            )
            .join("")}
        </select>
        ${errMsg}
      </div>
    `;
    }

    if (field.type === "chips") {
      return `
      <div class="${cls}">
        <label>${Utils.escape(field.label)}</label>
        <div class="choice-group">
          ${field.options
            .map(
              (opt, i) => `
            <label class="choice-chip ${opt.toLowerCase()}">
              <input type="radio" name="${field.name}" value="${Utils.escape(opt)}" ${i === 0 ? "checked" : ""}>
              <span class="choice-pill">${Utils.escape(opt)}</span>
            </label>
          `,
            )
            .join("")}
        </div>
        ${field.hint ? `<div class="field-hint">${Utils.escape(field.hint)}</div>` : ""}
      </div>
    `;
    }

    if (field.type === "textarea") {
      return `
      <div class="${cls}">
        <label>${Utils.escape(field.label)}</label>
        <textarea name="${field.name}" placeholder="${Utils.escape(field.placeholder || "")}" ${req}></textarea>
        ${errMsg}
      </div>
    `;
    }

    return `
    <div class="${cls}">
      <label>${Utils.escape(field.label)}</label>
      <input name="${field.name}" type="${field.type}"
             placeholder="${Utils.escape(field.placeholder || "")}" ${req} />
      ${errMsg}
    </div>
  `;
  },

  /* ── Enquiry Form ── */
  enquiryForm(fields) {
    const fieldsHTML = fields
      .map((f) => Components.formField(f))
      .join("");

    const content = `
    <div class="helper-note">
      <span>📋</span>
      <span>Fill all required fields. Select Payment Type as <strong>Finance</strong> or <strong>EMI</strong> to reveal finance details. Select Exchange as <strong>Yes</strong> or <strong>Maybe</strong> to reveal exchange details.</span>
    </div>
    <div style="height:16px;"></div>
    <form id="salesEnquiryForm" novalidate>
      <div class="form-grid">
        ${fieldsHTML}

        <div class="conditional-section" id="financeDetails">
          <div class="field">
            <label>Down Payment (₹)</label>
            <input name="downPayment" type="number" placeholder="Planned down payment" />
          </div>
          <div class="field">
            <label>EMI Amount (₹)</label>
            <input name="emi" type="number" placeholder="Expected monthly EMI" />
          </div>
          <div class="field">
            <label>Tenure (Months)</label>
            <input name="tenure" type="number" placeholder="Loan tenure in months" />
          </div>
          <div class="field">
            <label>Finance Company</label>
            <input name="whichFinance" type="text" placeholder="Preferred finance company" />
          </div>
        </div>

        <div class="conditional-section" id="exchangeDetails">
          <div class="field">
            <label>Exchange Type</label>
            <input name="exchangeType" type="text" placeholder="Scooter / Bike / Car" />
          </div>
          <div class="field">
            <label>Vehicle Model &amp; Make</label>
            <input name="vehicleModelMake" type="text" placeholder="Current vehicle details" />
          </div>
          <div class="field">
            <label>Year of Manufacturing</label>
            <input name="yearOfManufacturing" type="text" placeholder="e.g. 2019" />
          </div>
          <div class="field">
            <label>Owner Type</label>
            <input name="ownerType" type="text" placeholder="First / Second owner" />
          </div>
          <div class="field">
            <label>Valid Insurance</label>
            <select name="validInsurance">
              <option value="">Select</option>
              <option>Yes</option>
              <option>No</option>
            </select>
          </div>
          <div class="field">
            <label>Original RC Available</label>
            <select name="originalRcAvailable">
              <option value="">Select</option>
              <option>Yes</option>
              <option>No</option>
            </select>
          </div>
          <div class="field">
            <label>Customer Expected Exchange Price (₹)</label>
            <input name="expectedExchangePrice" type="number" placeholder="Customer expectation" />
          </div>
          <div class="field">
            <label>Price Offer by Dealer (₹)</label>
            <input name="dealerOfferPrice" type="number" placeholder="Dealer offer" />
          </div>
        </div>
      </div>

      <div class="form-actions">
        <button type="button" class="btn" data-nav="sales-enquiries">Cancel</button>
        <button type="reset" class="btn btn-secondary">Reset</button>
        <button type="submit" class="btn btn-primary">Submit Enquiry</button>
      </div>
    </form>
  `;

    return Components.card({
      title: "New Sales Enquiry Form",
      subtitle:
        "Capture customer interest, lead temperature, vehicle preference, and contact details.",
      content,
    });
  },

  /* ── List Stack ── */
  listStack(items) {
    return `
    <div class="list-stack">
      ${items
        .map(
          (item) => `
        <div class="list-item">
          <div>
            <strong>${Utils.escape(item.primary)}</strong>
            <span>${Utils.escape(item.secondary)}</span>
          </div>
          <span class="badge ${Utils.badgeClass(item.badge)}">${Utils.escape(item.badge)}</span>
        </div>
      `,
        )
        .join("")}
    </div>
  `;
  },
};

/* ═══════════════════════════════════════════════════════════════
 VIEWS
═══════════════════════════════════════════════════════════════ */
var Views = {
  dashboard() {
    const recentItems = Store.enquiries.slice(0, 4).map((item) => ({
      primary: `${item.customer} · ${item.vehicle}`,
      secondary: `${item.id} · ${item.source} · ${item.date}`,
      badge: item.status,
    }));

    const upcomingItems = Store.appointments
      .filter((a) => a.status === "Scheduled")
      .map((item) => ({
        primary: `${item.customer} · ${item.vehicle}`,
        secondary: `${item.id} · ${item.date} at ${item.time}`,
        badge: item.status,
      }));

    const hot = Store.enquiries.filter(
      (r) => r.temperature === "Hot",
    ).length;
    const warm = Store.enquiries.filter(
      (r) => r.temperature === "Warm",
    ).length;
    const cold = Store.enquiries.filter(
      (r) => r.temperature === "Cold",
    ).length;
    const total = Store.enquiries.length;
    const hotPct = total > 0 ? Math.round((hot / total) * 100) : 0;
    const warmPct = total > 0 ? Math.round((warm / total) * 100) : 0;
    const hotDeg = hotPct * 3.6;
    const warmDeg = warmPct * 3.6;

    const sources = {};
    Store.enquiries.forEach((r) => {
      sources[r.source] = (sources[r.source] || 0) + 1;
    });
    const sourceItems = Object.entries(sources).map(([src, count]) => ({
      primary: src,
      secondary: `${count} enquiries`,
      badge: `${total > 0 ? Math.round((count / total) * 100) : 0}%`,
    }));

    const leadDistContent = `
    <div style="display:flex;flex-direction:column;align-items:center;gap:16px;">
      <div style="width:180px;height:180px;border-radius:50%;background:conic-gradient(#dc2626 0deg ${hotDeg}deg,#ea580c ${hotDeg}deg ${hotDeg + warmDeg}deg,#2563eb ${hotDeg + warmDeg}deg 360deg);display:flex;align-items:center;justify-content:center;">
        <div style="width:120px;height:120px;background:white;border-radius:50%;display:flex;align-items:center;justify-content:center;flex-direction:column;font-weight:700;">
          <div style="font-size:22px;">${total}</div>
          <div style="font-size:11px;color:#64748b;">TOTAL LEADS</div>
        </div>
      </div>
      <div style="width:100%;max-width:220px;">
        <div style="display:flex;justify-content:space-between;margin-bottom:8px;"><span style="color:#dc2626;">🔴 Hot</span><span>${hot} (${hotPct}%)</span></div>
        <div style="display:flex;justify-content:space-between;margin-bottom:8px;"><span style="color:#ea580c;">🟠 Warm</span><span>${warm} (${warmPct}%)</span></div>
        <div style="display:flex;justify-content:space-between;"><span style="color:#2563eb;">🔵 Cold</span><span>${cold} (${total > 0 ? Math.round((cold / total) * 100) : 0}%)</span></div>
      </div>
    </div>
  `;

    const sourceContent = Components.listStack(sourceItems);

    return `
    <section class="page-header">
      <div class="page-title">
        <h2>Sales CRM Dashboard</h2>
        <p>Overview of your enquiries, appointments, and sales pipeline. All components are fully reusable and dynamically rendered.</p>
      </div>
      <div class="page-actions">
        <button class="btn btn-secondary" data-nav="sales-enquiries">View Enquiries</button>
        <button class="btn btn-primary" data-nav="enquiry-form">Add New Enquiry</button>
      </div>
    </section>
    ${Components.statCards()}
    <section class="split-grid">
      ${Components.card({ title: "Recent Enquiries", subtitle: "Latest sales activity in the pipeline", content: Components.listStack(recentItems), actionLabel: "Open Enquiries", actionView: "sales-enquiries" })}
      ${Components.card({ title: "Upcoming Appointments", subtitle: "Scheduled customer visits", content: Components.listStack(upcomingItems), actionLabel: "All Appointments", actionView: "appointments" })}
    </section>
    <section class="split-grid">
      ${Components.card({ title: "Lead Distribution", subtitle: "Temperature breakdown across pipeline", content: leadDistContent })}
      ${Components.card({ title: "Enquiry Sources", subtitle: "Where customers are coming from", content: sourceContent })}
    </section>
  `;
  },

  "sales-enquiries"() {
    return `
    <section class="page-header">
      <div class="page-title">
        <h2>Sales Enquiries</h2>
        <p>All customer enquiries with status, lead temperature, and vehicle details. Filter by status, vehicle, or date.</p>
      </div>
      <div class="page-actions">
        <button class="btn btn-primary" data-nav="enquiry-form">Add Enquiry</button>
      </div>
    </section>
    ${Components.table(TABLE_CONFIG.enquiries, Store.enquiries)}
  `;
  },

  appointments() {
    return `
    <section class="page-header">
      <div class="page-title">
        <h2>Appointment Booking</h2>
        <p>Track scheduled, pending, and completed customer appointments. Manage follow-up timing after enquiry capture.</p>
      </div>
      <div class="page-actions">
        <button class="btn btn-primary" data-nav="appointment-form">Add Appointment</button>
      </div>
    </section>
    ${Components.table(TABLE_CONFIG.appointments, Store.appointments)}
  `;
  },

  feedback() {
    return `
    <section class="page-header">
      <div class="page-title">
        <h2>Sales Feedback</h2>
        <p>Outcome records from customer appointments and discussions. Track submitted vs draft feedback entries.</p>
      </div>
    </section>
    ${Components.table(TABLE_CONFIG.feedback, Store.feedback)}
  `;
  },

  "enquiry-form"() {
    return `
    <section class="page-header">
      <div class="page-title">
        <h2>Enquiry Form</h2>
        <p>Capture complete customer details including contact information, vehicle interest, lead temperature, payment type, and address.</p>
      </div>
      <div class="page-actions">
        <button class="btn" data-nav="sales-enquiries">← Back to List</button>
      </div>
    </section>
    ${Components.enquiryForm(ENQUIRY_FORM_FIELDS)}
  `;
  },

  "appointment-form"() {
    return `
    <section class="page-header">
      <div class="page-title">
        <h2>New Appointment</h2>
        <p>Schedule a new customer appointment by filling in the details below.</p>
      </div>
      <div class="page-actions">
        <button class="btn" data-nav="appointments">← Back to List</button>
      </div>
    </section>
    <div class="card">
      <div class="card-header">
        <div>
          <h3>Appointment Details</h3>
          <p>Fill in all required fields to book the appointment.</p>
        </div>
      </div>
      <div class="card-body">
        <form id="appointmentForm" novalidate>
          <div class="form-grid">
            <div class="field">
              <label>Customer Name</label>
              <input type="text" name="apptCustomer" placeholder="Enter customer name" data-required="true" />
              <span class="error-msg">This field is required.</span>
            </div>
            <div class="field">
              <label>Vehicle</label>
              <input type="text" name="apptVehicle" placeholder="e.g. Fascino, FZ-S, R15" data-required="true" />
              <span class="error-msg">This field is required.</span>
            </div>
            <div class="field">
              <label>Date</label>
              <input type="date" name="apptDate" data-required="true" />
              <span class="error-msg">This field is required.</span>
            </div>
            <div class="field">
              <label>Time</label>
              <input type="time" name="apptTime" data-required="true" />
              <span class="error-msg">This field is required.</span>
            </div>
            <div class="field">
              <label>Status</label>
              <select name="apptStatus">
                <option value="Scheduled">Scheduled</option>
                <option value="Pending">Pending</option>
                <option value="Completed">Completed</option>
              </select>
            </div>
          </div>
          <div class="form-actions">
            <button type="reset" class="btn btn-secondary">Reset</button>
            <button type="submit" class="btn btn-primary">Book Appointment</button>
          </div>
        </form>
      </div>
    </div>
  `;
  },

  "director-dashboard"() {
    const report = Store.directorReport || {};
    const temperatureBreakdown = Array.isArray(
      report.temperature_breakdown,
    )
      ? report.temperature_breakdown
      : [];
    const sourceBreakdown = Array.isArray(report.source_breakdown)
      ? report.source_breakdown
      : [];
    const totalTemperature = temperatureBreakdown.reduce(
      (sum, item) => sum + Number(item.count || 0),
      0,
    );
    const topSourceCount = sourceBreakdown.reduce(
      (max, item) => Math.max(max, Number(item.count || 0)),
      0,
    );

    // Use real data from the backend report
    const metrics = [
      {
        label: "Total Enquiries",
        value: String(report.total_enquiries || 0),
        icon: "◔",
        trend: "-",
      },
      {
        label: "Appointments",
        value: String(report.total_appointments || 0),
        icon: "◫",
        trend: "-",
      },
      {
        label: "Feedbacks",
        value: String(report.total_feedback || 0),
        icon: "📝",
        trend: "-",
      },
      {
        label: "Conversion Rate",
        value: `${report.conversion_rate_percent || 0}%`,
        icon: "🎯",
        trend: "-",
      },
    ];

    const metricCards = metrics
      .map(
        (m) => `
      <section class="card stat-card">
        <div class="stat-top">
          <div>
            <small>${Utils.escape(m.label)}</small>
            <h3>${m.value}</h3>
          </div>
          <div class="stat-icon">${m.icon}</div>
        </div>
        <div class="trend">${Utils.escape(m.trend)}</div>
      </section>
    `,
      )
      .join("");

    return `
      <section class="page-header">
        <div class="page-title">
          <h2>Director Insights & Analytics</h2>
          <p>High-level performance metrics, sales conversion data, and pipeline breakdown.</p>
        </div>
        <div class="page-actions">
          <a href="../llm/Platinum_Sales_Chatbot-main/index.html" class="btn btn-primary">Open AI Strategy Chatbot</a>
        </div>
      </section>
      
      <div class="stats-grid">
        ${metricCards}
      </div>

      <section class="split-grid">
        ${Components.card({
          title: "Lead Temperature Mix",
          subtitle: "Live distribution for strategic pipeline review",
          content: temperatureBreakdown.length
            ? `<div style="display:flex; flex-direction:column; gap:14px;">
                ${temperatureBreakdown
                  .map((t) => {
                    const count = Number(t.count || 0);
                    const percent = totalTemperature
                      ? Math.round((count / totalTemperature) * 100)
                      : 0;
                    return `
                      <div>
                        <div style="display:flex; justify-content:space-between; gap:12px; margin-bottom:8px; font-weight:700;">
                          <span>${Utils.escape(t.temperature || "Unspecified")}</span>
                          <span>${Utils.escape(String(percent))}%</span>
                        </div>
                        <div style="height:10px; background:#e5e7eb; border-radius:999px; overflow:hidden;">
                          <div style="height:100%; width:${percent}%; background:#2563eb; border-radius:999px;"></div>
                        </div>
                      </div>
                    `;
                  })
                  .join("")}
              </div>`
            : `<div style="padding:12px;color:var(--muted);">No temperature analytics available.</div>`,
        })}
        ${Components.card({
          title: "Lead Source Momentum",
          subtitle:
            "Visual channel concentration across incoming enquiries",
          content: sourceBreakdown.length
            ? `<div style="display:grid; grid-template-columns:repeat(auto-fit,minmax(110px,1fr)); gap:12px;">
                ${sourceBreakdown
                  .map((s) => {
                    const count = Number(s.count || 0);
                    const height = topSourceCount
                      ? Math.max(
                          18,
                          Math.round((count / topSourceCount) * 84),
                        )
                      : 18;
                    return `
                      <div style="min-height:132px; display:flex; flex-direction:column; justify-content:flex-end; gap:8px;">
                        <div style="height:${height}px; background:#0f766e; border-radius:8px 8px 3px 3px;"></div>
                        <strong style="font-size:13px;">${Utils.escape(s.source || "Unspecified")}</strong>
                        <span style="color:var(--muted); font-size:12px;">${Utils.escape(String(count))} enquiries</span>
                      </div>
                    `;
                  })
                  .join("")}
              </div>`
            : `<div style="padding:12px;color:var(--muted);">No source analytics available.</div>`,
        })}
      </section>
    `;
  },

  reports() {
    const report = Store.directorReport || {};
    const temps = Array.isArray(report.temperature_breakdown)
      ? report.temperature_breakdown
      : [];
    const sources = Array.isArray(report.source_breakdown)
      ? report.source_breakdown
      : [];

    return `
      <section class="page-header">
        <div class="page-title">
          <h2>Executive Reports</h2>
          <p>Backend-driven sales performance breakdowns for director review.</p>
        </div>
        <div class="page-actions">
          <button class="btn btn-primary" onclick="window.print()">Export Report</button>
        </div>
      </section>
      <div class="card">
        <div class="card-header">
          <div>
            <h3>Lead Temperature Report</h3>
            <p>Enquiries grouped by backend temperature data.</p>
          </div>
        </div>
        <div class="card-body">
          <div style="overflow-x: auto;">
            <table class="data-table">
              <thead>
                <tr><th>Temperature</th><th>Count</th></tr>
              </thead>
              <tbody>
                ${
                  temps.length > 0
                    ? temps
                        .map(
                          (t) => `
                  <tr>
                    <td>${Utils.escape(t.temperature || "Unspecified")}</td>
                    <td>${Utils.escape(String(t.count || 0))}</td>
                  </tr>
                `,
                        )
                        .join("")
                    : '<tr><td colspan="2" style="text-align:center;">No temperature data found.</td></tr>'
                }
              </tbody>
            </table>
          </div>
        </div>
      </div>
      <div class="card">
        <div class="card-header">
          <div>
            <h3>Enquiry Source Report</h3>
            <p>Lead sources grouped by backend enquiry data.</p>
          </div>
        </div>
        <div class="card-body">
          <div style="overflow-x: auto;">
            <table class="data-table">
              <thead>
                <tr><th>Source</th><th>Count</th></tr>
              </thead>
              <tbody>
                ${
                  sources.length > 0
                    ? sources
                        .map(
                          (s) => `
                  <tr>
                    <td>${Utils.escape(s.source || "Unspecified")}</td>
                    <td>${Utils.escape(String(s.count || 0))}</td>
                  </tr>
                `,
                        )
                        .join("")
                    : '<tr><td colspan="2" style="text-align:center;">No source data found.</td></tr>'
                }
              </tbody>
            </table>
          </div>
        </div>
      </div>
    `;
  },

  "admin-controls"() {
    const uniqueUsers = new Set(
      Store.adminLogs.map((l) => l.user).filter(Boolean),
    );
    const activeUsers = uniqueUsers.size;

    return `
      <section class="page-header">
        <div class="page-title">
          <h2>System Administration</h2>
          <p>Review administrative activity from the secured backend audit log.</p>
        </div>
      </section>

      <div class="stats-grid">
        <section class="card stat-card">
          <div class="stat-top">
            <div><small>Active Users</small><h3>${Utils.escape(String(activeUsers))}</h3></div>
            <div class="stat-icon">👥</div>
          </div>
          <div class="trend">${Utils.escape(`${Store.adminLogs.length} recent audit events`)}</div>
        </section>
        <section class="card stat-card">
          <div class="stat-top">
            <div><small>Audit Events</small><h3>${Utils.escape(String(Store.adminLogs.length))}</h3></div>
            <div class="stat-icon">📈</div>
          </div>
          <div class="trend">${Utils.escape("Loaded from /api/admin/logs/")}</div>
        </section>
        <section class="card stat-card">
          <div class="stat-top">
            <div><small>Admin Endpoint</small><h3>Secured</h3></div>
            <div class="stat-icon">🗄</div>
          </div>
          <div class="trend">${Utils.escape("403 for non-admin roles")}</div>
        </section>
      </div>

      <section class="card">
        <div class="card-header">
          <div>
            <h3>Security Audit Log</h3>
            <p>Recent administrative actions and authentication events.</p>
          </div>
        </div>
        <div class="card-body">
          <div style="overflow-x: auto;">
            <table class="data-table">
              <thead>
                <tr><th>Timestamp</th><th>User</th><th>Action</th><th>Target</th><th>Details</th></tr>
              </thead>
              <tbody>
                ${
                  Store.adminLogs.length > 0
                    ? Store.adminLogs
                        .map(
                          (log) => `
                  <tr>
                    <td>${Utils.escape(log.timestamp)}</td>
                    <td>${Utils.escape(log.user || "System")}</td>
                    <td>${Utils.escape(log.action_flag)}</td>
                    <td>${Utils.escape(log.object || "-")}</td>
                    <td>${Utils.escape(log.change_message || "-")}</td>
                  </tr>
                `,
                        )
                        .join("")
                    : '<tr><td colspan="5" style="text-align:center;">No audit logs found.</td></tr>'
                }
              </tbody>
            </table>
          </div>
        </div>
      </section>
    `;
  },

  "access-denied"() {
    const userRole = Auth.getUserRole() || "Unknown";
    const attemptedRoute = appState.deniedRoute || "this module";

    return `
      <div class="card" style="max-width: 500px; margin: 80px auto; text-align: center; overflow: visible;">
        <div class="card-body" style="padding: 40px 30px;">
          <div style="width: 64px; height: 64px; background: #fef2f2; color: #dc2626; border-radius: 20px; display: flex; align-items: center; justify-content: center; font-size: 28px; margin: -72px auto 20px auto; border: 4px solid var(--bg); box-shadow: 0 4px 12px rgba(220, 38, 38, 0.15);">
            🔒
          </div>
          <h2 style="font-size: 22px; margin: 0 0 12px; font-weight: 800; letter-spacing: -0.02em;">403 Access Restricted</h2>
          <p style="color: var(--muted); line-height: 1.6; margin-bottom: 24px; font-size: 14px;">
            Your current role (<strong style="text-transform: capitalize; color: var(--text);">${Utils.escape(userRole)}</strong>) 
            does not have permission to view <strong>${Utils.escape(attemptedRoute)}</strong>.
          </p>
          <button class="btn btn-primary" onclick="Router.navigate(DEFAULT_ROUTE_BY_ROLE[Auth.getUserRole()] || 'dashboard')" style="width: 100%;">
            Return to Workspace
          </button>
        </div>
      </div>
    `;
  },
};

/* ═══════════════════════════════════════════════════════════════
 ROUTER
═══════════════════════════════════════════════════════════════ */
var Router = {
  navigate(viewId) {
    if (!Auth.requireValidSession()) return;
    const userRole = Auth.getUserRole();
    const target = resolveNavigationTarget(viewId, userRole);

    // Role-based route guard
    if (!target.allowed) {
      Utils.toast("Access Denied: Insufficient Permissions", "error");
      appState.currentView = "access-denied";
      appState.deniedRoute = target.deniedRoute;

      if (window.innerWidth <= 900) {
        appState.mobileSidebarOpen = false;
        Shell.sync();
      }
      window.history.replaceState(null, null, "#access-denied");
      Persist.saveUI();
      Renderer.page();
      window.scrollTo({ top: 0, behavior: "smooth" });
      return;
    }

    appState.currentView = target.viewId;
    if (target.viewId !== "access-denied") {
      window.history.replaceState(null, null, "#" + target.viewId);
    }
    if (window.innerWidth <= 900) {
      appState.mobileSidebarOpen = false;
      Shell.sync();
    }
    Persist.saveUI();
    Renderer.page();
    window.scrollTo({ top: 0, behavior: "smooth" });
  },
};

/* ═══════════════════════════════════════════════════════════════
 SHELL
═══════════════════════════════════════════════════════════════ */
var Shell = {
  sync() {
    const shell = document.getElementById("appShell");
    shell.classList.toggle(
      "sidebar-collapsed",
      appState.sidebarCollapsed && window.innerWidth > 900,
    );
    shell.classList.toggle(
      "mobile-sidebar-open",
      appState.mobileSidebarOpen && window.innerWidth <= 900,
    );
  },
};

/* ═══════════════════════════════════════════════════════════════
 RENDERER
═══════════════════════════════════════════════════════════════ */
var Renderer = {
  sidebar() {
    document.getElementById("sidebar").innerHTML = Components.sidebar();
    document.querySelectorAll("[data-nav]").forEach((el) => {
      const view = el.dataset.nav;
      if (!view) return;
      const handler = () => Router.navigate(view);
      el.addEventListener("click", handler);
      el.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") handler();
      });
    });
  },

  topbar() {
    document.getElementById("topbar").innerHTML = Components.topbar();

    document
      .getElementById("sidebarToggle")
      .addEventListener("click", () => {
        if (window.innerWidth <= 900) {
          appState.mobileSidebarOpen = !appState.mobileSidebarOpen;
        } else {
          appState.sidebarCollapsed = !appState.sidebarCollapsed;
        }
        Shell.sync();
        Persist.saveUI();
      });

    document
      .getElementById("globalSearch")
      .addEventListener("input", (e) => {
        appState.search = e.target.value;
        Persist.saveUI();
        Renderer.pageContent();
      });

    const avatarBtn = document.getElementById("avatarBtn");
    const profileMenu = document.getElementById("profileMenu");
    avatarBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      const isOpen = profileMenu.classList.toggle("open");
      avatarBtn.setAttribute("aria-expanded", isOpen);
    });
    document.addEventListener("click", () => {
      profileMenu.classList.remove("open");
      avatarBtn.setAttribute("aria-expanded", "false");
    });

    // Logout button
    const logoutBtn = document.getElementById("logoutBtn");
    if (logoutBtn) {
      logoutBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        Auth.logoutUser();
      });
    }
  },

  pageContent() {
    const root = document.getElementById("pageRoot");
    const viewFn = Views[appState.currentView] || Views.dashboard;
    root.innerHTML = viewFn.call(Views);
    Renderer.bindPageEvents();
  },

  page(rerenderTopbar = true) {
    this.pageContent();
    if (rerenderTopbar) this.topbar();
    this.sidebar();
  },

  bindPageEvents() {
    /* data-nav on any element navigates to the target view */
    document.querySelectorAll("[data-nav]").forEach((el) => {
      if (el.closest(".sidebar")) return; // sidebar handles its own
      const view = el.dataset.nav;
      if (!view) return;
      el.addEventListener("click", () => Router.navigate(view));
    });

    /* Table filter dropdowns */
    document.querySelectorAll("[data-filter]").forEach((control) => {
      control.addEventListener("change", () => {
        const tableKey = control.dataset.filter;
        const filterKey = control.dataset.filterKey;
        if (appState.filters[tableKey]) {
          appState.filters[tableKey][filterKey] = control.value;
        }
        Persist.saveUI();
        Renderer.pageContent();
        Renderer.sidebar(); // keep active state
      });
    });

    /* Form behaviour */
    this.bindForm();
  },

  bindForm() {
    const form = document.getElementById("salesEnquiryForm");

    /* ── Appointment Form ── */
    const apptForm = document.getElementById("appointmentForm");
    if (apptForm) {
      const apptValidate = () => {
        let valid = true;
        apptForm
          .querySelectorAll('[data-required="true"]')
          .forEach((el) => {
            const empty = !el.value.trim();
            const parent = el.closest(".field");
            if (parent) parent.classList.toggle("has-error", empty);
            el.classList.toggle("error", empty);
            if (empty) valid = false;
          });
        return valid;
      };

      apptForm
        .querySelectorAll('[data-required="true"]')
        .forEach((el) => {
          el.addEventListener("input", () => {
            if (el.value.trim()) {
              const parent = el.closest(".field");
              if (parent) parent.classList.remove("has-error");
              el.classList.remove("error");
            }
          });
        });

      apptForm.addEventListener("submit", async (e) => {
        e.preventDefault();

        if (!apptValidate()) {
          Utils.toast("Please fill all required fields.", "error");
          return;
        }

        const get = (name) =>
          apptForm.querySelector(`[name="${name}"]`)?.value?.trim() || "";
        const rawTime = get("apptTime");
        const [h, m] = rawTime.split(":").map(Number);
        const suffix = h >= 12 ? "PM" : "AM";
        const hour12 = h % 12 || 12;
        const formattedTime = `${String(hour12).padStart(2, "0")}:${String(m).padStart(2, "0")} ${suffix}`;

        const payload = {
          id: `SABP-${Date.now()}`,
          customer: get("apptCustomer"),
          vehicle: get("apptVehicle"),
          date: get("apptDate"),
          time: formattedTime,
          status: get("apptStatus") || "Scheduled",
        };

        try {
          const saved = await Api.createAppointment(payload);

          const mapped = {
            id: saved.appointment_id,
            customer: saved.customer,
            vehicle: saved.vehicle,
            date: saved.date,
            time: saved.time,
            status: saved.status,
          };

          Store.addAppointment(mapped);

          Utils.toast(
            `Appointment booked for ${mapped.customer} on ${mapped.date} at ${mapped.time}.`,
            "success",
          );

          Router.navigate("appointments");
        } catch (error) {
          console.error("Create appointment failed:", error);
          Utils.toast(
            error.message || "Failed to save appointment to server.",
            "error",
          );
        }
      });
    }

    if (!form) return;

    /* Conditional field visibility */
    const conditionalMap = {
      financeDetails: (val) => val === "finance" || val === "emi",
      exchangeDetails: (val) => val === "yes" || val === "maybe",
    };

    form.querySelectorAll("[data-conditional]").forEach((select) => {
      const targetId = select.dataset.conditional;
      const target = document.getElementById(targetId);
      const test = conditionalMap[targetId] || (() => false);

      const toggle = () => {
        if (target)
          target.classList.toggle(
            "show",
            test((select.value || "").toLowerCase()),
          );
      };
      select.addEventListener("change", toggle);
      toggle();
    });

    /* Inline validation */
    const validate = () => {
      let valid = true;
      form.querySelectorAll('[data-required="true"]').forEach((el) => {
        const empty = !el.value.trim();
        const parent = el.closest(".field");
        if (parent) parent.classList.toggle("has-error", empty);
        el.classList.toggle("error", empty);
        if (empty) valid = false;
      });
      return valid;
    };

    form.querySelectorAll('[data-required="true"]').forEach((el) => {
      el.addEventListener("input", () => {
        if (el.value.trim()) {
          const parent = el.closest(".field");
          if (parent) parent.classList.remove("has-error");
          el.classList.remove("error");
        }
      });
    });

    /* Submit */
    form.addEventListener("submit", async (e) => {
      e.preventDefault();

      if (!validate()) {
        Utils.toast("Please fill all required fields.", "error");
        return;
      }

      const get = (name) =>
        form.querySelector(`[name="${name}"]`)?.value?.trim() || "";
      const getChecked = (name) =>
        form.querySelector(`[name="${name}"]:checked`)?.value || "Hot";

      const payload = {
        id: `SE-${String(Date.now()).slice(-5)}`,
        customer: get("customerName") || "Customer",
        vehicle: get("modelName") || "Selected model",
        temperature: getChecked("leadTemperature"),
        status: get("salesEnquiryStatus") || "Submitted",
        date: new Date().toISOString().slice(0, 10),
        source: get("enquirySource") || "Walk-in",
      };

      try {
        const saved = await Api.createEnquiry(payload);

        const mapped = {
          id: saved.enquiry_id,
          customer: saved.customer,
          vehicle: saved.vehicle,
          temperature: saved.temperature,
          status: saved.status,
          date: saved.date,
          source: saved.source,
        };

        Store.addEnquiry(mapped);

        Utils.toast(
          `Enquiry for ${mapped.customer} submitted. Lead: ${mapped.temperature} | ${mapped.vehicle}`,
          "success",
        );

        Router.navigate("sales-enquiries");
      } catch (error) {
        console.error("Create enquiry failed:", error);
        Utils.toast(
          error.message || "Failed to save enquiry to server.",
          "error",
        );
      }
    });

    /* Reset */
    form.addEventListener("reset", () => {
      setTimeout(() => {
        form
          .querySelectorAll(".conditional-section")
          .forEach((el) => el.classList.remove("show"));
        form
          .querySelectorAll(".error")
          .forEach((el) => el.classList.remove("error"));
        form
          .querySelectorAll(".field")
          .forEach((f) => f.classList.remove("has-error"));
      }, 10);
    });
  },
};

/* ═══════════════════════════════════════════════════════════════
 INIT
═══════════════════════════════════════════════════════════════ */
async function init() {
  Persist.loadUI();

  window.addEventListener("hashchange", () => {
    const hash = window.location.hash.replace("#", "");
    if (
      hash &&
      hash !== appState.currentView &&
      hash !== "access-denied"
    ) {
      Router.navigate(hash);
    }
  });

  // Auth MUST be initialized before any protected data is loaded.
  // initializeAuth() shows the login page if no valid session exists
  // and wires up the login form. Data loading only proceeds when authenticated.
  await Auth.initializeAuth();

  // Only load backend data if the user is authenticated
  if (
    Auth.isAuthenticated() &&
    appState.currentView !== "access-denied"
  ) {
    await Actions.refreshAll();
  }

  Renderer.topbar();
  Renderer.pageContent();
  Renderer.sidebar();
  Shell.sync();
  window.addEventListener("resize", Shell.sync.bind(Shell));
}

// In standard browser environment, trigger init automatically.
// In Node (testing) environment, we let the test helper control init.
if (typeof window !== "undefined" && typeof window.addEventListener !== "undefined" && !window.__TESTING__) {
  init();
}

// Export for coverage / Jest context if running in Node module loader
if (typeof module !== "undefined" && module.exports) {
  module.exports = {
    Auth, Api, appState, Store, Actions, ROUTE_CONFIG, NAV_CONFIG,
    DEFAULT_ROUTE_BY_ROLE, VALID_ROLES, ROUTE_REDIRECTS_BY_ROLE,
    resolveRouteForRole, resolveNavigationTarget, ENQUIRY_FORM_FIELDS,
    TABLE_CONFIG, Utils, Components, Views, Router, Shell, Renderer, init, Persist
  };
}
