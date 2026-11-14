// Keep the original Frappe forms, listeners, reset flow and two-factor handling.
(function () {
  async function decorate() {
    if (!['', '/login'].includes(location.pathname.replace(/\/$/, '')) || document.body.classList.contains('sisu-login')) return;
    const login = document.querySelector('.for-login');
    if (!login) return;
    let entry = {};
    try {
      const response = await fetch('/api/method/institute_lms.portal_entry.public', {credentials:'same-origin'});
      if (response.ok) entry = (await response.json()).message || {};
    } catch (_) { /* Native login remains available if presentation metadata is unavailable. */ }
    if (entry.control_plane && location.pathname === '/') {
      location.replace('/login?redirect-to=/campus' + location.hash);
      return;
    }
    document.body.classList.add('sisu-login');
    const host = login.parentElement;
    const layout = document.createElement('div'); layout.className = 'sisu-login-layout';
    host.parentNode.insertBefore(layout, host);
    const story = document.createElement('aside'); story.className = 'sisu-login-story';
    story.innerHTML = '<a href="/campus" class="sisu-login-brand" aria-label="SISU home"><img src="/assets/institute_lms/login-sisu-logo.png" alt="SISU"></a><div class="sisu-login-copy"><small>GOOD PEOPLE. BRIGHT FUTURES.</small><h1>Learning is better.<br>Together.</h1><p>Meet your people. Share what you know.<br>Build something brighter together.</p></div><img class="sisu-login-art" src="/assets/institute_lms/login-community.png" alt="A learning community"><footer><strong>More than lessons. A place to belong.</strong><p>Learn · Connect · Grow</p></footer>';
    layout.appendChild(story);layout.appendChild(host);host.classList.add('sisu-login-forms');
    const back = document.createElement('a');back.href='/campus';back.className='sisu-login-back';back.textContent='← Back to sign in';host.insertBefore(back,host.firstChild);
    const heading=login.querySelector('.page-card-head h4, .page-card-head h2');if(heading)heading.textContent='Welcome back.';
    const intro=login.querySelector('.page-card-head p');if(intro)intro.textContent='Sign in to your SISU learning or teaching workspace.';
    if (entry.control_plane) {
      document.body.classList.add('sisu-owner-login');
      document.title = 'Platform owner sign in | SISU';
      back.remove();
      if (heading) heading.textContent = 'Platform owner sign in';
      if (intro) intro.textContent = 'Manage SISU organizations, subscriptions and platform settings.';
      const brand = story.querySelector('.sisu-login-brand').cloneNode(true);
      brand.href = '/login?redirect-to=/campus';
      brand.setAttribute('aria-label', 'SISU platform owner sign in');
      host.insertBefore(brand, host.firstChild);
      if (entry.student_campus_url) {
        const footer = document.createElement('div'); footer.className = 'sisu-owner-campus';
        const hint = document.createElement('p'); hint.textContent = 'Here to learn?';
        const campus = document.createElement('a'); campus.className = 'sisu-owner-campus-link';
        campus.href = entry.student_campus_url; campus.textContent = 'Go to student campus';
        footer.append(hint, campus); host.appendChild(footer);
      }
    }
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',decorate);else decorate();
})();
