// Keep the original Frappe forms, listeners, reset flow and two-factor handling.
(function () {

  function installPasswordRecoveryTransport() {
    const nativeCall = window.login?.call;
    if (!nativeCall) return;
    window.login.call = function (args, callback, url = '/', errorMessage = null) {
      if (args?.cmd !== 'frappe.core.doctype.user.user.reset_password') {
        return nativeCall.call(this, args, callback, url, errorMessage);
      }
      // The marketing root is static; password recovery must reach Frappe.
      const pending = nativeCall.call(this, args, callback,
        '/api/method/frappe.core.doctype.user.user.reset_password', errorMessage);
      pending?.fail?.(() => {
        window.login.show_error_banner('Unable to request a reset link. Please try again shortly.');
      });
      pending?.always?.(() => window.login.hide_loading());
      return pending;
    };
  }
  function protectResetLinkFromAutofill() {
    if (location.pathname.replace(/\/$/, '') !== '/update-password' ||
        !new URLSearchParams(location.search).get('key')) return;
    const oldPassword = document.getElementById('old_password');
    if (!oldPassword?.form) return;
    // A reset link authenticates this flow; an autofilled hidden old password
    // must not be treated as user input. Server-side reuse checks still apply.
    oldPassword.disabled = true;
    oldPassword.autocomplete = 'off';
    const clearUnusedPassword = () => { oldPassword.value = ''; };
    clearUnusedPassword();
    for (const event of ['input', 'change', 'keyup', 'paste', 'submit']) {
      oldPassword.form.addEventListener(event, clearUnusedPassword, true);
    }
    window.addEventListener('pageshow', clearUnusedPassword);
  }

  function decorate() {
    if (!['', '/login', '/update-password'].includes(location.pathname.replace(/\/$/, ''))) return;
    const login = document.querySelector('.for-login, .for-reset-password');
    if (!login) return;
    // Replace the tiny, mouse-only framework SVG with a native keyboard button.
    const hidePasswords = [];
    document.querySelectorAll('.password-field .toggle-password').forEach(icon => {
      const input = document.querySelector(icon.getAttribute('toggle'));
      if (!input || !input.id) return;
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'sisu-password-toggle';
      button.setAttribute('aria-controls', input.id);
      const fieldName = (input.labels?.[0]?.textContent || 'password').trim().toLowerCase();
      function setVisible(visible) {
        input.type = visible ? 'text' : 'password';
        button.textContent = visible ? 'Hide' : 'Show';
        button.setAttribute('aria-label', (visible ? 'Hide ' : 'Show ') + fieldName);
      }
      setVisible(false);
      button.addEventListener('click', () => setVisible(input.type === 'password'));
      input.form?.addEventListener('reset', () => setVisible(false));
      hidePasswords.push(() => setVisible(false));
      icon.replaceWith(button);
    });
    window.addEventListener('hashchange', () => hidePasswords.forEach(hide => hide()));
    window.addEventListener('pageshow', () => hidePasswords.forEach(hide => hide()));
    const reset = login.classList.contains('for-reset-password');
    const entry = {
      control_plane: document.body.classList.contains('sisu-owner-login'),
      student_campus_url: document.querySelector('meta[name="sisu-student-campus"]')?.content || ''
    };
    function routeSignup() {
      if (location.hash !== '#signup') return false;
      location.replace(entry.control_plane ? '/login?redirect-to=/campus' : '/campus');
      return true;
    }
    if (routeSignup()) return;
    window.addEventListener('hashchange', routeSignup);
    if (entry.control_plane && location.pathname === '/') {
      location.replace('/login?redirect-to=/campus' + location.hash);
      return;
    }
    const heading=login.querySelector('.page-card-head h4, .page-card-head h2');if(heading)heading.textContent=reset ? 'Set your password' : 'Welcome back.';
    const intro=login.querySelector('.page-card-head p');if(intro)intro.textContent=reset ? 'Choose a strong password for your SISU account.' : 'Sign in to your SISU learning or teaching workspace.';
    const loginParams = new URLSearchParams(location.search);
    if (!entry.control_plane && !reset && loginParams.get('role') === 'teacher') {
      if (heading) heading.textContent = 'Teacher sign in';
      if (intro) intro.textContent = 'Sign in to open your teaching workspace.';
    }
    if (!entry.control_plane && !reset && loginParams.get('signup_success') === 'teacher') {
      // A one-time presentation notice; it never grants authentication or access.
      loginParams.delete('signup_success');
      history.replaceState(history.state, '', location.pathname + '?' + loginParams.toString() + location.hash);
      const dialog = document.createElement('dialog');
      dialog.className = 'sisu-signup-success';
      dialog.setAttribute('aria-labelledby', 'sisu-signup-success-title');
      dialog.setAttribute('aria-describedby', 'sisu-signup-success-description');
      const title = document.createElement('h2');
      title.id = 'sisu-signup-success-title';
      title.textContent = 'Signup successful';
      const description = document.createElement('p');
      description.id = 'sisu-signup-success-description';
      description.textContent = 'Your teacher account has been created. Please log in to continue.';
      const ok = document.createElement('button');
      ok.type = 'button';
      ok.textContent = 'OK';
      ok.addEventListener('click', () => dialog.close());
      dialog.addEventListener('close', () => {
        dialog.remove();
        login.querySelector('#login_email')?.focus();
      });
      dialog.append(title, description, ok);
      document.body.append(dialog);
      dialog.showModal();
      ok.focus();
    }
    document.querySelectorAll('.for-reset-password .sign-up-message a').forEach(link => { link.href = '/login?redirect-to=/campus'; });
    const emailHeading = document.querySelector('.for-login-with-email-link .page-card-head h4');
    if (emailHeading) emailHeading.textContent = 'Sign in with an email link';
    if (entry.control_plane) {
      document.title = reset ? 'Set your password | SISU' : 'Platform owner sign in | SISU';
      if (heading && !reset) heading.textContent = 'Platform owner sign in';
      if (intro && !reset) intro.textContent = 'Manage SISU organizations, subscriptions and platform settings.';
      window.frappe?.ready(() => {
        const handlers = window.login?.login_handlers;
        if (!handlers) return;
        const nativeError = handlers[401];
        let timer, retryUntil = 0;
        const password = login.querySelector('#login_password');
        password?.form?.addEventListener('submit', event => {
          if (Date.now() < retryUntil) { event.preventDefault(); event.stopImmediatePropagation(); }
        }, true);
        handlers[401] = function (xhr, data) {
          const response = xhr?.responseJSON || data || xhr;
          const seconds = Number(response?.mfa_retry_after_seconds);
          if (!Number.isFinite(seconds) || seconds < 1 || seconds > 60) return nativeError(xhr, data);
          window.login.hide_loading();
          login.querySelector('.login-error-banner')?.classList.add('hidden');
          let notice = login.querySelector('.sisu-mfa-cooldown');
          if (!notice && password) {
            notice = document.createElement('p');
            notice.className = 'sisu-mfa-cooldown';
            notice.setAttribute('role', 'status');
            (password.closest('.form-group') || password.parentElement).after(notice);
          }
          const submit = password?.form?.querySelector('.btn-login, button[type="submit"], .es-button[data-variant="solid"]');
          retryUntil = Date.now() + seconds * 1000;
          clearInterval(timer);
          function tick() {
            const remaining = Math.max(0, Math.ceil((retryUntil - Date.now()) / 1000));
            if (notice) notice.textContent = remaining ? `You can request another code in 00:${String(remaining).padStart(2, '0')}.` : 'You can request a new code now. Select Continue.';
            if (submit) submit.disabled = remaining > 0;
            if (!remaining) clearInterval(timer);
          }
          tick(); timer = setInterval(tick, 1000);
        };
      });
      // Frappe inserts the OTP form after the password request. Enhance that
      // existing form without replacing its input, submit button or listeners.
      function decorateVerification() {
        const panel = login.querySelector('#twofactor_div');
        document.body.classList.toggle('sisu-mfa-screen', !!panel);
        if (!panel || panel.dataset.sisuMfa) return;
        const input = panel.querySelector('#login_token');
        const button = panel.querySelector('#verify_token');
        if (!input || !button) return;
        panel.dataset.sisuMfa = '1';
        const head = panel.querySelector('.page-card-head');
        if (head) {
          head.replaceChildren();
          const title = document.createElement('h2');
          title.textContent = 'Verify your sign-in';
          const description = document.createElement('p');
          description.textContent = 'One more step to open your admin workspace.';
          head.append(title, description);
        }
        const label = document.createElement('label');
        label.htmlFor = input.id;
        label.className = 'sisu-mfa-label';
        label.textContent = 'SMS verification code';
        input.before(label);
        input.inputMode = 'numeric';
        input.autocomplete = 'one-time-code';
        input.maxLength = 6;
        input.pattern = '[0-9]{6}';
        input.placeholder = '••••••';
        input.setAttribute('aria-describedby', 'sisu-mfa-hint');
        input.addEventListener('input', () => { input.value = input.value.replace(/\D/g, '').slice(0, 6); });
        input.addEventListener('paste', event => {
          const digits = event.clipboardData?.getData('text').replace(/\D/g, '');
          if (digits?.length === 6) { event.preventDefault(); input.value = digits; input.dispatchEvent(new Event('input', { bubbles: true })); }
        });
        const hint = document.createElement('p');
        hint.id = 'sisu-mfa-hint';
        hint.textContent = 'Enter or paste the 6-digit code. It expires in 5 minutes.';
        input.after(hint);
        button.type = 'submit';
        button.textContent = 'Verify and sign in';
        const back = document.createElement('a');
        back.className = 'sisu-mfa-back';
        back.href = '/login?redirect-to=/campus';
        back.textContent = 'Back to sign in';
        const help = document.createElement('p');
        help.className = 'sisu-mfa-help';
        help.textContent = 'Need a new code? Go back and sign in again after one minute.';
        panel.append(back, help);
      }
      new MutationObserver(decorateVerification).observe(login, { childList: true, subtree: true });
      decorateVerification();
    }
  }
  // This script is included after the native forms. Layout is already rendered by Jinja.
  protectResetLinkFromAutofill();
  decorate();
  window.frappe?.ready(installPasswordRecoveryTransport);
})();
