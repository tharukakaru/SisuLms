// Keep the original Frappe forms, listeners, reset flow and two-factor handling.
(function () {
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
    document.querySelectorAll('.for-reset-password .sign-up-message a').forEach(link => { link.href = '/login?redirect-to=/campus'; });
    const emailHeading = document.querySelector('.for-login-with-email-link .page-card-head h4');
    if (emailHeading) emailHeading.textContent = 'Sign in with an email link';
    if (entry.control_plane) {
      document.title = reset ? 'Set your password | SISU' : 'Platform owner sign in | SISU';
      if (heading && !reset) heading.textContent = 'Platform owner sign in';
      if (intro && !reset) intro.textContent = 'Manage SISU organizations, subscriptions and platform settings.';
    }
  }
  // This script is included after the native forms. Layout is already rendered by Jinja.
  decorate();
})();
