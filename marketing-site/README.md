# SISU public website integration

Static pages: /, /students/, /teachers/, /institutes/, /contact/.
Signup links open /campus?signup=1 on the same host. Portal links open /campus.
Serve app.js, CSS and assets beneath /marketing/ to avoid overriding Frappe /assets/.
Keep /campus, /api/, /login and /assets/frappe/ routed to the existing Frappe site.
Do not replace the entire server configuration with a static-site fallback.

The contact form only stores local drafts. It does not submit enquiries.
Media/testimonial placeholders require content review before publication.
Server integration and live verification have not been performed.
