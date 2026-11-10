import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import crypto from 'node:crypto'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const DB_PATH = path.resolve(__dirname, '..', '.local-dev-db.json')

function todayISO() {
  return new Date().toLocaleDateString('en-CA', { timeZone: 'Asia/Colombo' })
}

function defaultSeed() {
  const today = todayISO()
  const institutes = [
    {
      name: 'inst-sisudemo',
      code: 'SISUDEMO',
      title: 'SISU Practice Institute',
      language: 'en',
      white_label: false,
      billing_day: 1,
    },
    {
      name: 'inst-ind-teacher',
      code: 'SISUTESTTC',
      title: 'Independent Teacher Workspace',
      language: 'en',
      white_label: false,
      billing_day: 1,
    },
  ]

  const classrooms = [
    {
      name: 'room-math-101',
      institute: 'inst-sisudemo',
      title: 'Combined Mathematics — Pure & Applied',
      subject: 'Combined Mathematics',
      class_kind: 'General',
      teaching_medium: 'English',
      grade: 'A/L',
      teacher: 'mem-teacher-1',
      teacher_name: 'Nadeesha Perera',
      teacher_id: 'SISU-TC-000003',
      owner_type: 'Institute',
      owner_user: 'institute@admin.com',
      teacher_access: 'Full control',
      fee_mode: 'Free',
      fee: 0,
      billing_type: 'Monthly',
      access_duration_days: 30,
      published: 1,
      active: 1,
      students: 24,
      tag: 'A/L 2027',
      color: 'violet',
      font: 'sans',
      exam_date: '2027-08-15',
      motivation: 'Small steps every day',
      description: 'Interactive A/L Combined Mathematics covering calculus, statics, and dynamics.',
      state: 'unlocked',
      access: { allowed: true, reason: 'Enrolled' },
    },
    {
      name: 'room-phys-202',
      institute: 'inst-sisudemo',
      title: 'Physics Revision & Past Papers',
      subject: 'Physics',
      class_kind: 'Revision',
      teaching_medium: 'English',
      grade: 'A/L',
      teacher: 'mem-teacher-1',
      teacher_name: 'Nadeesha Perera',
      teacher_id: 'SISU-TC-000003',
      owner_type: 'Teacher',
      owner_user: 'teacher@admin.com',
      teacher_access: 'Full control',
      fee_mode: 'Paid',
      fee: 3500,
      billing_type: 'Monthly',
      access_duration_days: 30,
      published: 1,
      active: 1,
      students: 18,
      tag: 'Revision',
      color: 'indigo',
      font: 'sans',
      exam_date: '2027-08-20',
      motivation: 'Master the fundamentals',
      description: 'Structured weekly past paper discussions and mechanics mastery.',
      state: 'unlocked',
      access: { allowed: true, reason: 'Enrolled' },
    },
  ]

  const sessions = [
    {
      name: 'sess-1',
      classroom: 'room-math-101',
      title: 'Differential Calculus — Chain Rule & Tangents',
      starts_at: `${today}T16:00:00`,
      ends_at: `${today}T18:00:00`,
      mode: 'Online',
      meeting_provider: 'LiveKit',
      status: 'Scheduled',
      location: 'Online Live Room',
      description: 'Bring your past paper booklet (2019–2025).',
    },
    {
      name: 'sess-2',
      classroom: 'room-phys-202',
      title: 'Simple Harmonic Motion & Waves',
      starts_at: `${today}T18:30:00`,
      ends_at: `${today}T20:00:00`,
      mode: 'Online',
      meeting_provider: 'YouTube',
      status: 'Scheduled',
      location: 'Online Studio',
      description: 'Oscillations, pendulum derivations, and MCQ speed drill.',
    },
  ]

  const users = {
    'student@admin.com': {
      email: 'student@admin.com',
      password: '1234',
      role: 'Student',
      shared_campus: false,
      onboarding_kind: 'Student',
      phone_verified: true,
      phone: '+94771234567',
      member: {
        name: 'ST-SISUDEMO-00001',
        user: 'student@admin.com',
        full_name: 'Kavindi Jayawardena',
        role: 'Student',
        active: 1,
        institute: 'inst-sisudemo',
        phone: '+94771234567',
        language: 'en',
      },
      profile: {
        name: 'prof-student-1',
        user: 'student@admin.com',
        username: 'kavindi_j',
        display_name: 'Kavindi Jayawardena',
        kind: 'Student',
        country: 'Sri Lanka',
        status: 'Verified',
        lms_id: 'SISU-ST-000001',
        bio: 'A/L Physical Science student passionate about mathematics and robotics.',
        grades: 'Advanced Level (Grades 12–13)',
        languages: 'English, Sinhala',
        socials: {},
      },
    },
    'teacher@admin.com': {
      email: 'teacher@admin.com',
      password: '1234',
      role: 'Teacher',
      shared_campus: false,
      onboarding_kind: 'Teacher',
      phone_verified: true,
      phone: '+94772345678',
      member: {
        name: 'mem-teacher-1',
        user: 'teacher@admin.com',
        full_name: 'Nadeesha Perera',
        role: 'Teacher',
        institute_teacher: false,
        active: 1,
        institute: 'inst-ind-teacher',
        phone: '+94772345678',
        language: 'en',
      },
      profile: {
        name: 'prof-teacher-1',
        user: 'teacher@admin.com',
        username: 'nadeesha_math',
        display_name: 'Nadeesha Perera',
        kind: 'Teacher',
        independent: true,
        country: 'Sri Lanka',
        status: 'Verified',
        lms_id: 'SISU-TC-000003',
        qualifications: 'BSc (Hons) Engineering, University of Moratuwa',
        curriculum: 'Combined Mathematics, Physics',
        tagline: 'Clarity in every derivation.',
        bio: 'Independent Combined Mathematics & Physics educator with 8+ years of A/L teaching experience.',
        grades: 'Advanced Level (Grades 12–13)',
        languages: 'English, Sinhala',
        socials: {},
      },
    },
    'instituteteacher@admin.com': {
      email: 'instituteteacher@admin.com',
      password: '1234',
      role: 'Teacher',
      shared_campus: false,
      onboarding_kind: 'Teacher',
      phone_verified: true,
      phone: '+94773456789',
      member: {
        name: 'mem-teacher-2',
        user: 'instituteteacher@admin.com',
        full_name: 'Kasun Rajapaksha',
        role: 'Teacher',
        institute_teacher: true,
        active: 1,
        institute: 'inst-sisudemo',
        phone: '+94773456789',
        language: 'en',
      },
      profile: {
        name: 'prof-teacher-2',
        user: 'instituteteacher@admin.com',
        username: 'kasun_physics',
        display_name: 'Kasun Rajapaksha',
        kind: 'Teacher',
        independent: false,
        country: 'Sri Lanka',
        status: 'Verified',
        lms_id: 'SISU-TC-000004',
        qualifications: 'BSc (Hons) Physics, University of Colombo',
        curriculum: 'Physics',
        bio: 'Assigned institute physics lecturer at SISU Practice Institute.',
        grades: 'Advanced Level (Grades 12–13)',
        languages: 'English',
        socials: {},
      },
    },
    'institute@admin.com': {
      email: 'institute@admin.com',
      password: '1234',
      role: 'Admin',
      shared_campus: false,
      onboarding_kind: 'Institute',
      phone_verified: true,
      phone: '+94774567890',
      member: {
        name: 'mem-admin-1',
        user: 'institute@admin.com',
        full_name: 'SISU Practice Institute Admin',
        role: 'Admin',
        active: 1,
        institute: 'inst-sisudemo',
        phone: '+94774567890',
        language: 'en',
      },
      profile: {
        name: 'prof-inst-1',
        user: 'institute@admin.com',
        username: 'sisu_demo_institute',
        display_name: 'SISU Practice Institute',
        kind: 'Institute',
        country: 'Sri Lanka',
        status: 'Verified',
        lms_id: 'SISU-IN-000001',
        workspace: 'inst-sisudemo',
        tagline: 'Where curious minds grow together.',
        bio: 'Leading multi-subject academy for O/L and A/L learners across Sri Lanka.',
        curriculum: 'Mathematics, Science, Physics, Chemistry, ICT',
        grades: 'Advanced Level (Grades 12–13)',
        languages: 'English, Sinhala, Tamil',
        socials: {},
      },
    },
    'superadmin@admin.com': {
      email: 'superadmin@admin.com',
      password: '1234',
      role: 'Super Admin',
      shared_campus: false,
      control_plane: false,
      onboarding_kind: 'Super Admin',
      phone_verified: true,
      phone: '+94770000001',
      member: null,
      profile: null,
    },
    'onboarding@admin.com': {
      email: 'onboarding@admin.com',
      password: '1234',
      role: 'Teacher',
      shared_campus: false,
      onboarding_kind: 'Teacher',
      phone_verified: false,
      phone: '+94779998887',
      member: null,
      profile: null,
    },
    'switcher@admin.com': {
      email: 'switcher@admin.com',
      password: '1234',
      role: 'Teacher',
      shared_campus: true,
      workspace_choices_required: true,
      onboarding_kind: 'Teacher',
      phone_verified: true,
      phone: '+94778887776',
      member: null,
      profile: {
        name: 'prof-switcher-1',
        user: 'switcher@admin.com',
        username: 'amaya_fernando',
        display_name: 'Amaya Fernando',
        kind: 'Teacher',
        independent: true,
        country: 'Sri Lanka',
        status: 'Verified',
        lms_id: 'SISU-TC-000009',
        bio: 'Teaching across multiple institutes and independent classes.',
        socials: {},
      },
    },
    'gate@admin.com': {
      email: 'gate@admin.com',
      password: '1234',
      role: 'Teacher',
      shared_campus: false,
      onboarding_kind: 'Teacher',
      subscription_available: false,
      phone_verified: true,
      phone: '+94776665554',
      member: {
        name: 'mem-gate-1',
        user: 'gate@admin.com',
        full_name: 'Dilshan Silva',
        role: 'Teacher',
        active: 1,
        institute: 'inst-ind-teacher',
        phone: '+94776665554',
        language: 'en',
      },
      profile: null,
    },
  }

  // Alias staging/public test emails to the same accounts with password '1234'
  users['sisu.student.test@gmail.com'] = {
    ...users['student@admin.com'],
    email: 'sisu.student.test@gmail.com',
  }
  users['sisu.student.test+teacher@gmail.com'] = {
    ...users['teacher@admin.com'],
    email: 'sisu.student.test+teacher@gmail.com',
  }
  users['qa.teacher@sisuacademylk.com'] = {
    ...users['teacher@admin.com'],
    email: 'qa.teacher@sisuacademylk.com',
  }
  users['sisu.student.test+institute.teacher@gmail.com'] = {
    ...users['instituteteacher@admin.com'],
    email: 'sisu.student.test+institute.teacher@gmail.com',
  }
  users['sisu.student.test+institute.admin@gmail.com'] = {
    ...users['institute@admin.com'],
    email: 'sisu.student.test+institute.admin@gmail.com',
  }
  users['qa.institute@sisuacademylk.com'] = {
    ...users['institute@admin.com'],
    email: 'qa.institute@sisuacademylk.com',
  }
  users['tharukakarunarathne60@gmail.com'] = {
    ...users['superadmin@admin.com'],
    email: 'tharukakarunarathne60@gmail.com',
  }

  return {
    institutes,
    classrooms,
    sessions,
    users,
    challenges: {},
    applications: [],
    joinRequests: [],
    notifications: [
      {
        name: 'notif-1',
        subject: 'Welcome to your local SISU workspace',
        creation: `${today} 09:00`,
        body: 'Your local development database is active and ready for testing.',
        email_content: 'Your local development database is active and ready for testing.',
        event_type: 'welcome',
        read: 0,
        read_at: null,
      },
    ],
    invoices: [
      {
        name: 'INV-2026-0001',
        classroom: 'room-phys-202',
        classroom_title: 'Physics Revision & Past Papers',
        student: 'ST-SISUDEMO-00001',
        student_name: 'Kavindi Jayawardena',
        amount: 3500,
        status: 'Paid',
        due_date: today,
        billing_month: today.slice(0, 7),
      },
    ],
  }
}

export function loadDb() {
  try {
    if (fs.existsSync(DB_PATH)) {
      const raw = JSON.parse(fs.readFileSync(DB_PATH, 'utf8'))
      if (raw && raw.users) return raw
    }
  } catch {}
  const seed = defaultSeed()
  saveDb(seed)
  return seed
}

export function saveDb(db) {
  try {
    fs.writeFileSync(DB_PATH, JSON.stringify(db, null, 2), 'utf8')
  } catch {}
}

function parseCookies(cookieHeader = '') {
  const out = {}
  cookieHeader.split(';').forEach((pair) => {
    const idx = pair.indexOf('=')
    if (idx > 0) {
      const k = pair.slice(0, idx).trim()
      const v = decodeURIComponent(pair.slice(idx + 1).trim())
      out[k] = v
    }
  })
  return out
}

function readBody(req) {
  return new Promise((resolve) => {
    const chunks = []
    req.on('data', (c) => chunks.push(c))
    req.on('end', () => {
      const raw = Buffer.concat(chunks).toString('utf8')
      if (!raw) return resolve({})
      const ct = req.headers['content-type'] || ''
      if (ct.includes('application/x-www-form-urlencoded')) {
        return resolve(Object.fromEntries(new URLSearchParams(raw)))
      }
      try {
        resolve(JSON.parse(raw))
      } catch {
        resolve(Object.fromEntries(new URLSearchParams(raw)))
      }
    })
  })
}

function sendJson(res, status, payload, extraHeaders = {}) {
  const body = JSON.stringify(payload)
  res.writeHead(status, {
    'Content-Type': 'application/json; charset=utf-8',
    'Cache-Control': 'no-store',
    ...extraHeaders,
  })
  res.end(body)
}

function sendError(res, status, message, extra = {}) {
  const serverMsg = JSON.stringify([JSON.stringify({ message })])
  sendJson(res, status, {
    exc_type: 'ValidationError',
    _server_messages: serverMsg,
    message,
    ...extra,
  })
}

export function sisuLocalDevDbPlugin() {
  const db = loadDb()

  return {
    name: 'sisu-local-dev-db',
    configureServer(server) {
      server.middlewares.use(async (req, res, next) => {
        if (process.env.SISU_USE_REMOTE === '1') return next()

        const urlObj = new URL(req.url || '/', 'http://127.0.0.1:5178')
        const pathname = urlObj.pathname

        // Handle GET/POST /logout or /api/method/logout
        if (pathname === '/logout' || pathname === '/api/method/logout') {
          const clearCookie = 'sisu_local_sid=; Path=/; HttpOnly; Max-Age=0; SameSite=Lax'
          if (req.method === 'GET') {
            res.writeHead(302, {
              'Set-Cookie': clearCookie,
              Location: '/campus',
            })
            res.end()
            return
          }
          sendJson(res, 200, { message: 'Logged Out' }, { 'Set-Cookie': clearCookie })
          return
        }

        // Handle POST /api/method/login
        if (pathname === '/api/method/login' && req.method === 'POST') {
          const body = await readBody(req)
          const email = String(body.usr || '').trim().toLowerCase()
          const pwd = String(body.pwd || '')
          const user = db.users[email]
          if (!user || (user.password !== pwd && pwd !== '1234')) {
            sendError(
              res,
              401,
              'Invalid login credentials. Try student@admin.com, teacher@admin.com, institute@admin.com, or superadmin@admin.com (password: 1234).'
            )
            return
          }
          const cookie = `sisu_local_sid=${encodeURIComponent(user.email)}; Path=/; HttpOnly; SameSite=Lax`
          sendJson(
            res,
            200,
            { message: 'Logged In', home_page: '/campus', full_name: user.member?.full_name || user.email },
            { 'Set-Cookie': cookie }
          )
          return
        }

        // Handle POST /api/method/frappe.core.doctype.user.user.reset_password
        if (pathname === '/api/method/frappe.core.doctype.user.user.reset_password') {
          sendJson(res, 200, { message: 'Password reset link sent (local dev mode).' })
          return
        }

        // Handle /api/method/institute_lms.<module>.<method>
        if (!pathname.startsWith('/api/method/institute_lms.')) {
          return next()
        }

        const routePart = pathname.slice('/api/method/institute_lms.'.length)
        const [moduleName, methodName] = routePart.split('.')
        const queryArgs = Object.fromEntries(urlObj.searchParams)
        const bodyArgs = req.method === 'POST' ? await readBody(req) : {}
        const args = { ...queryArgs, ...bodyArgs }

        const cookies = parseCookies(req.headers.cookie || '')
        const sidEmail = (cookies.sisu_local_sid || '').toLowerCase()
        const currentUser = sidEmail && db.users[sidEmail] ? db.users[sidEmail] : null

        const key = `${moduleName}.${methodName}`

        // 1. Session & Policy
        if (key === 'portal_session.current') {
          if (!currentUser) {
            sendJson(res, 200, {
              message: {
                authenticated: false,
                user: 'Guest',
                csrf_token: 'local-dev-csrf-token',
              },
            })
            return
          }
          sendJson(res, 200, {
            message: {
              authenticated: true,
              user: currentUser.email,
              role: currentUser.role,
              member: currentUser.member || null,
              shared_campus: Boolean(currentUser.shared_campus),
              control_plane: Boolean(currentUser.control_plane),
              onboarding_kind: currentUser.onboarding_kind || currentUser.role,
              workspace_choices_required: Boolean(currentUser.workspace_choices_required),
              csrf_token: 'local-dev-csrf-token',
            },
          })
          return
        }

        if (key === 'portal_policy.public') {
          sendJson(res, 200, {
            message: {
              privacy_policy_url: 'https://www.sisuacademylk.com/privacy/',
              privacy_policy_version: 'public-2026-11-02-v1',
              provider_applications_enabled: true,
              google_available: true,
              self_signup_enabled: true,
            },
          })
          return
        }

        if (key === 'portal_policy.google_start') {
          const targetUser = db.users['student@admin.com']
          const cookie = `sisu_local_sid=${encodeURIComponent(targetUser.email)}; Path=/; HttpOnly; SameSite=Lax`
          sendJson(
            res,
            200,
            {
              message: {
                simulated_user: targetUser.email,
                url: 'https://accounts.google.com/o/oauth2/v2/auth?simulated=1',
              },
            },
            { 'Set-Cookie': cookie }
          )
          return
        }

        // 2. Account Billing & Capabilities
        if (key === 'account_billing.status') {
          const available = currentUser?.subscription_available !== false
          sendJson(res, 200, {
            message: {
              gateway_ready: false,
              account: {
                available,
                workspace_available: available,
                plan: 'Gold',
                state: available ? 'active' : 'past_due',
                status: available ? 'Active' : 'Trial ended',
                trial_until: '2027-12-31',
              },
            },
          })
          return
        }

        if (key === 'full_api.capabilities') {
          sendJson(res, 200, {
            message: {
              plan: 'Gold',
              state: 'active',
              locked_reason: '',
              premium_ai: true,
              organization_available: true,
              entitlements: { lms: true, live: true, papers: true, ai: true },
              features: { lms: true, live: true, papers: true, ai: true },
            },
          })
          return
        }

        // 3. Verified Self-Signup & Public Signup (Student / Teacher / Institute)
        if (key === 'public_signup.start' || key === 'self_signup.start') {
          const rawData = typeof args.data === 'string' ? JSON.parse(args.data) : args.data || args
          const token = 'local-challenge-' + crypto.randomBytes(16).toString('hex')
          db.challenges[token] = {
            details: rawData,
            email_verified: false,
            phone_verified: false,
          }
          saveDb(db)
          sendJson(res, 200, { message: { challenge: token } })
          return
        }

        if (key === 'public_signup.verify' || key === 'self_signup.verify') {
          const ch = db.challenges[args.token]
          if (ch) {
            if (args.channel === 'email') ch.email_verified = true
            if (args.channel === 'phone') ch.phone_verified = true
            saveDb(db)
          }
          sendJson(res, 200, { message: { verified: true } })
          return
        }

        if (key === 'public_signup.send_phone' || key === 'self_signup.send_phone') {
          sendJson(res, 200, { message: { sent: true } })
          return
        }

        if (key === 'public_signup.complete' || key === 'self_signup.complete') {
          const ch = db.challenges[args.token]
          const details = ch?.details || {}
          const email = String(details.email || 'newuser@admin.com').trim().toLowerCase()
          const kindMap = {
            Student: 'Student',
            'Individual Teacher': 'Teacher',
            Institute: 'Admin',
          }
          const role = kindMap[details.kind] || 'Student'
          const fullName =
            details.organization ||
            `${details.first_name || 'SISU'} ${details.last_name || 'Member'}`.trim()
          db.users[email] = {
            email,
            password: String(args.password || '1234'),
            role,
            shared_campus: false,
            onboarding_kind: role === 'Admin' ? 'Institute' : role,
            phone_verified: true,
            phone: details.phone || '+94771234567',
            member: {
              name: `MEM-${Date.now()}`,
              user: email,
              full_name: fullName,
              role,
              active: 1,
              institute: 'inst-sisudemo',
              phone: details.phone || '+94771234567',
              language: 'en',
            },
            profile: {
              name: `prof-${Date.now()}`,
              user: email,
              username: details.username || email.split('@')[0].replace(/[^a-z0-9_]/g, '_'),
              display_name: fullName,
              kind: role === 'Admin' ? 'Institute' : role,
              country: details.country || 'Sri Lanka',
              status: 'Verified',
              lms_id: `SISU-${role.slice(0, 2).toUpperCase()}-${Math.floor(100000 + Math.random() * 900000)}`,
              bio: details.bio || '',
              qualifications: details.qualifications || '',
              grades: details.grade || 'Advanced Level (Grades 12–13)',
              languages: 'English',
              socials: {},
            },
          }
          saveDb(db)
          sendJson(res, 200, {
            message: {
              created: true,
              message: `Account created in local DB (${email}). You can now sign in with your password!`,
            },
          })
          return
        }

        // 4. Provider Registration Flow
        if (key === 'registration.status') {
          sendJson(res, 200, { message: { status: 'None' } })
          return
        }

        if (key === 'registration.submit') {
          const data = typeof args.data === 'string' ? JSON.parse(args.data) : args.data || {}
          const email = String(data.email || '').trim().toLowerCase()
          const role = data.account_type === 'Institute' ? 'Admin' : 'Teacher'
          if (email && !db.users[email]) {
            db.users[email] = {
              email,
              password: '1234',
              role,
              shared_campus: false,
              onboarding_kind: data.account_type === 'Institute' ? 'Institute' : 'Teacher',
              phone_verified: true,
              phone: data.phone || '+94771234567',
              member: {
                name: `MEM-${Date.now()}`,
                user: email,
                full_name: data.organization || data.full_name || email,
                role,
                active: 1,
                institute: 'inst-sisudemo',
                phone: data.phone || '+94771234567',
                language: 'en',
              },
            }
          }
          db.applications.push({ ...data, status: 'Pending', created_at: new Date().toISOString() })
          saveDb(db)
          sendJson(res, 200, {
            message: {
              status: 'Pending',
              account_type: data.account_type || 'Individual Teacher',
              request: 'REG-LOCAL-' + db.applications.length,
            },
          })
          return
        }

        if (key === 'registration.confirm_account') {
          sendJson(res, 200, { message: { confirmed: true } })
          return
        }

        if (key === 'registration.account_unread') {
          const unread = db.notifications.filter((n) => !n.read).length
          sendJson(res, 200, { message: { count: unread } })
          return
        }

        if (key === 'registration.account_status') {
          sendJson(res, 200, {
            message: {
              verified: true,
              full_name: currentUser?.member?.full_name || currentUser?.email || 'SISU Student',
            },
          })
          return
        }

        if (key === 'registration.account_notifications') {
          sendJson(res, 200, { message: db.notifications })
          return
        }

        if (key === 'registration.read_account_notice') {
          const row = db.notifications.find((n) => n.name === args.name)
          if (row) {
            row.read = 1
            saveDb(db)
          }
          sendJson(res, 200, { message: { read: true } })
          return
        }

        // 5. Mobile Verification
        if (key === 'mobile_verification.status') {
          sendJson(res, 200, {
            message: {
              verified: Boolean(currentUser?.phone_verified),
              phone: currentUser?.phone || '+94771234567',
              cooldown_seconds: 0,
              sms_available: true,
              whatsapp_available: true,
            },
          })
          return
        }

        if (key === 'mobile_verification.start') {
          if (currentUser && args.phone) {
            currentUser.phone = args.phone
            saveDb(db)
          }
          sendJson(res, 200, {
            message: {
              sent: true,
              phone: args.phone || currentUser?.phone || '+94771234567',
              cooldown_seconds: 60,
              notice: 'Local Dev Mode: Enter 123456 as your verification code.',
            },
          })
          return
        }

        if (key === 'mobile_verification.verify') {
          if (currentUser) {
            currentUser.phone_verified = true
            saveDb(db)
          }
          sendJson(res, 200, {
            message: {
              verified: true,
              phone: currentUser?.phone || '+94771234567',
            },
          })
          return
        }

        // 6. Campus Switcher & Institute Join
        if (key === 'campus_context.choices') {
          sendJson(res, 200, {
            message: {
              selected: currentUser?.member?.institute || '',
              institutes: [
                {
                  institute: 'inst-sisudemo',
                  title: 'SISU Practice Institute',
                  code: 'SISUDEMO',
                  role: currentUser?.role === 'Admin' ? 'Admin' : 'Teacher',
                  student_number: currentUser?.role === 'Student' ? 'ST-SISUDEMO-00001' : '',
                },
                {
                  institute: 'inst-ind-teacher',
                  title: 'Independent Teacher Workspace',
                  code: 'SISUTESTTC',
                  role: 'Teacher',
                  student_number: '',
                },
              ],
            },
          })
          return
        }

        if (key === 'campus_context.select') {
          if (currentUser) {
            const instId = args.institute || 'inst-sisudemo'
            currentUser.shared_campus = false
            currentUser.workspace_choices_required = false
            currentUser.subscription_available = true
            currentUser.member = currentUser.member || {
              name: `MEM-${Date.now()}`,
              user: currentUser.email,
              full_name: currentUser.profile?.display_name || 'Amaya Fernando',
              role: currentUser.role === 'Admin' ? 'Admin' : 'Teacher',
              institute_teacher: instId === 'inst-sisudemo' && currentUser.role === 'Teacher',
              active: 1,
              institute: instId,
              language: 'en',
            }
            currentUser.member.institute = instId
            saveDb(db)
          }
          sendJson(res, 200, { message: { selected: args.institute || 'inst-sisudemo' } })
          return
        }

        if (key === 'campus_context.clear') {
          if (currentUser) {
            currentUser.shared_campus = true
            currentUser.workspace_choices_required = false
            currentUser.member = null
            saveDb(db)
          }
          sendJson(res, 200, { message: { cleared: true } })
          return
        }

        if (key === 'campus_join.institutes') {
          sendJson(res, 200, {
            message: [
              {
                name: 'prof-inst-1',
                display_name: 'SISU Practice Institute',
                username: 'sisu_demo_institute',
                tagline: 'Leading A/L & O/L Academy in Colombo',
              },
            ],
          })
          return
        }

        if (key === 'campus_join.my_requests') {
          sendJson(res, 200, { message: db.joinRequests })
          return
        }

        if (key === 'campus_join.request_join') {
          const row = {
            name: 'JOIN-' + (db.joinRequests.length + 1),
            profile: args.institute_profile,
            institute_name: 'SISU Practice Institute',
            status: 'Pending',
            purpose: args.purpose || 'New application',
          }
          db.joinRequests.push(row)
          saveDb(db)
          sendJson(res, 200, { message: row })
          return
        }

        if (key === 'campus_join.register_student') {
          sendJson(res, 200, {
            message: {
              student_number: 'ST-SISUDEMO-00001',
              institute: 'inst-sisudemo',
            },
          })
          return
        }

        // 7. Profiles
        if (key === 'profiles.me') {
          sendJson(res, 200, {
            message: {
              phone_verified: Boolean(currentUser?.phone_verified),
              profile: currentUser?.profile || null,
            },
          })
          return
        }

        if (key === 'profiles.save_profile') {
          const data = args.data || {}
          if (currentUser) {
            currentUser.profile = {
              ...(currentUser.profile || {}),
              ...data,
              user: currentUser.email,
              status: 'Verified',
              lms_id: currentUser.profile?.lms_id || 'SISU-ID-000100',
            }
            if (!currentUser.member) {
              const role = currentUser.onboarding_kind === 'Institute' ? 'Admin' : currentUser.onboarding_kind || 'Teacher'
              currentUser.member = {
                name: `MEM-${Date.now()}`,
                user: currentUser.email,
                full_name: data.display_name || currentUser.email,
                role,
                active: 1,
                institute: 'inst-sisudemo',
                language: 'en',
              }
            }
            saveDb(db)
          }
          sendJson(res, 200, { message: currentUser?.profile || data })
          return
        }

        if (key === 'profiles.search' || key === 'campus_join.people') {
          const allProfiles = Object.values(db.users)
            .map((u) => u.profile)
            .filter(Boolean)
          const unique = Array.from(new Map(allProfiles.map((p) => [p.name, p])).values())
          sendJson(res, 200, { message: unique })
          return
        }

        if (key === 'profiles.follow_status') {
          sendJson(res, 200, { message: [] })
          return
        }

        if (key === 'profiles.followed_updates') {
          sendJson(res, 200, {
            message: [
              {
                name: 'news-1',
                display_name: 'SISU Practice Institute',
                headline: 'New A/L 2027 Combined Mathematics Intake Open',
                body: 'Live interactive classes every week with full recording access.',
              },
            ],
          })
          return
        }

        if (key === 'profiles.followed_classes') {
          sendJson(res, 200, {
            message: db.classrooms.map((c) => ({
              ...c,
              provider_name: 'SISU Practice Institute',
              demo: true,
              unlocked: true,
            })),
          })
          return
        }

        // 8. Core Workspace Bootstrap & Dashboard
        if (key === 'api.bootstrap') {
          const member = currentUser?.member || {
            name: 'ST-SISUDEMO-00001',
            user: currentUser?.email || 'student@admin.com',
            full_name: 'Kavindi Jayawardena',
            role: currentUser?.role || 'Student',
            active: 1,
            institute: 'inst-sisudemo',
          }
          const inst =
            db.institutes.find((i) => i.name === member.institute) || db.institutes[0]
          sendJson(res, 200, {
            message: {
              member: {
                ...member,
                provider_profile: currentUser?.profile || {
                  kind: member.role === 'Admin' ? 'Institute' : member.role,
                  status: 'Verified',
                },
              },
              institute: inst,
              payment_provider: 'payments.lk',
            },
          })
          return
        }

        if (key === 'api.dashboard_summary') {
          sendJson(res, 200, {
            message: {
              classrooms: db.classrooms.length,
              students: 42,
              teachers: 4,
              sessions_today: db.sessions.length,
              unpaid_invoices: 0,
              progress: [
                { subject: 'Combined Mathematics', completed: 8, total: 12 },
                { subject: 'Physics', completed: 5, total: 10 },
              ],
            },
          })
          return
        }

        if (key === 'api.classrooms') {
          if (Number(args.deleted) === 1) {
            sendJson(res, 200, { message: db.classrooms.filter((c) => !c.active) })
            return
          }
          sendJson(res, 200, { message: db.classrooms.filter((c) => c.active !== 0) })
          return
        }

        if (key === 'api.classroom_detail') {
          const room =
            db.classrooms.find((c) => c.name === args.name) || db.classrooms[0]
          sendJson(res, 200, {
            message: {
              room: {
                ...room,
                permissions: {
                  can_edit: currentUser?.role !== 'Student',
                  can_teach: currentUser?.role !== 'Student',
                  can_delete: currentUser?.role === 'Admin' || currentUser?.role === 'Teacher',
                },
              },
              access: { allowed: true, reason: 'Enrolled' },
              sessions: db.sessions.filter((s) => s.classroom === room.name),
              materials: [
                {
                  name: 'mat-1',
                  classroom: room.name,
                  title: 'Week 1 — Calculus Fundamentals & Worked Examples.pdf',
                  kind: 'Link',
                  url: 'https://www.sisuacademylk.com',
                  description: 'Complete formula sheet and tutorial problems.',
                },
              ],
              feedback: [],
              announcements: [
                {
                  name: 'ann-1',
                  headline: 'Welcome to the new term!',
                  body: 'All live session recordings and tutorial sheets are posted in this classroom.',
                  creation: todayISO(),
                },
              ],
            },
          })
          return
        }

        if (key === 'api.schedule') {
          sendJson(res, 200, { message: db.sessions })
          return
        }

        if (key === 'api.news') {
          sendJson(res, 200, {
            message: [
              {
                name: 'news-1',
                headline: 'A/L 2027 Combined Mathematics & Physics Term 1 Schedule',
                description: 'Weekly live lessons and past paper discussions are now open.',
                starts_on: todayISO(),
                ends_on: todayISO(),
              },
            ],
          })
          return
        }

        if (key === 'api.invoices') {
          sendJson(res, 200, { message: db.invoices })
          return
        }

        if (key === 'api.members') {
          const members = Object.values(db.users)
            .map((u) => u.member)
            .filter(Boolean)
          sendJson(res, 200, { message: members })
          return
        }

        if (key === 'api.teachers') {
          sendJson(res, 200, {
            message: [
              { name: 'mem-teacher-1', full_name: 'Nadeesha Perera', user: 'teacher@admin.com' },
              { name: 'mem-teacher-2', full_name: 'Kasun Rajapaksha', user: 'instituteteacher@admin.com' },
            ],
          })
          return
        }

        if (key === 'api.enrollments') {
          sendJson(res, 200, {
            message: [
              {
                name: 'ENR-0001',
                classroom: args.classroom || 'room-math-101',
                student: 'ST-SISUDEMO-00001',
                student_name: 'Kavindi Jayawardena',
                active: 1,
                access_override: 'Automatic',
              },
            ],
          })
          return
        }

        if (key === 'api.save_classroom') {
          const data = args.data || args
          const newRoom = {
            name: data.name || `room-${Date.now()}`,
            institute: currentUser?.member?.institute || 'inst-sisudemo',
            title: data.title || 'New Classroom',
            subject: data.subject || 'General',
            class_kind: data.class_kind || 'General',
            teaching_medium: data.teaching_medium || 'English',
            grade: data.grade || 'A/L',
            teacher: data.teacher || 'mem-teacher-1',
            teacher_name: currentUser?.member?.full_name || 'Nadeesha Perera',
            owner_type: currentUser?.role === 'Admin' ? 'Institute' : 'Teacher',
            fee_mode: data.fee_mode || 'Free',
            fee: Number(data.fee || 0),
            published: 1,
            active: 1,
            students: 1,
            tag: data.subject || 'Class',
            color: 'violet',
            font: 'sans',
            state: 'unlocked',
            access: { allowed: true, reason: 'Enrolled' },
          }
          const idx = db.classrooms.findIndex((c) => c.name === newRoom.name)
          if (idx >= 0) db.classrooms[idx] = { ...db.classrooms[idx], ...newRoom }
          else db.classrooms.push(newRoom)
          saveDb(db)
          sendJson(res, 200, { message: newRoom.name })
          return
        }

        if (key === 'api.save_session') {
          const data = args.data || args
          const sess = {
            name: data.name || `sess-${Date.now()}`,
            classroom: data.classroom || db.classrooms[0]?.name,
            title: data.title || 'New Live Session',
            starts_at: data.starts_at || `${todayISO()}T16:00`,
            ends_at: data.ends_at || `${todayISO()}T18:00`,
            mode: data.mode || 'Online',
            meeting_provider: data.meeting_provider || 'LiveKit',
            status: 'Scheduled',
            description: data.description || '',
          }
          db.sessions.push(sess)
          saveDb(db)
          sendJson(res, 200, { message: sess.name })
          return
        }

        // 9. Teacher & Institute Provider Home
        if (key === 'teaching.overview') {
          sendJson(res, 200, {
            message: {
              today: todayISO(),
              students: 42,
              teachers: 4,
              pending_slips: 1,
              classrooms: db.classrooms,
              upcoming: db.sessions,
              memberships: [
                {
                  name: 'rel-1',
                  status: 'Active',
                  user: 'instituteteacher@admin.com',
                  person: db.users['instituteteacher@admin.com']?.profile,
                },
              ],
            },
          })
          return
        }

        if (key === 'commercial.metrics') {
          const today = todayISO()
          sendJson(res, 200, {
            message: {
              start_date: today.slice(0, 8) + '01',
              end_date: today,
              classrooms: db.classrooms,
              scheduled_completed_hours: [{ classroom: 'room-math-101', hours: 18.5 }],
              monthly_collections: [
                { month: 'Sep 2026', gross_minor: 8500000 },
                { month: 'Oct 2026', gross_minor: 11200000 },
                { month: 'Nov 2026', gross_minor: 14500000 },
              ],
              collections: [
                {
                  classroom: 'room-phys-202',
                  payment_channel: 'Bank transfer',
                  payments: 18,
                  students: 18,
                  gross_minor: 6300000,
                },
              ],
            },
          })
          return
        }

        if (key === 'classroom_handover.listing') {
          sendJson(res, 200, { message: [] })
          return
        }

        if (key === 'invitations.list_invitations') {
          sendJson(res, 200, { message: [] })
          return
        }

        if (key === 'catalog.publishing_options') {
          sendJson(res, 200, {
            message: [
              {
                name: 'prof-inst-1',
                display_name: 'SISU Practice Institute',
                kind: 'Institute',
              },
            ],
          })
          return
        }

        if (key === 'learning_spaces.choices' || key === 'public_student.choices') {
          sendJson(res, 200, {
            message: [
              {
                name: 'prof-inst-1',
                title: 'SISU Practice Institute',
                display_name: 'SISU Practice Institute',
                code: 'SISUDEMO',
              },
            ],
          })
          return
        }

        if (key === 'learning_spaces.classes' || key === 'public_student.classes') {
          sendJson(res, 200, {
            message: {
              classes: db.classrooms.map((c) => ({ ...c, state: 'unlocked' })),
              has_more: false,
            },
          })
          return
        }

        if (key === 'programme_courses.student_programmes' || key === 'teaching.programmes') {
          sendJson(res, 200, { message: [] })
          return
        }

        if (key === 'notification_service.inbox') {
          sendJson(res, 200, { message: db.notifications })
          return
        }

        if (key === 'release.unread') {
          const unread = db.notifications.filter((n) => !n.read).length
          sendJson(res, 200, { message: { count: unread } })
          return
        }

        // 10. Super Admin / Owner Workspace
        if (key === 'portal_session.overview') {
          sendJson(res, 200, {
            message: {
              students: 128,
              teachers: 14,
              institutes: 3,
              pending_profiles: db.applications.length,
              pending_payouts: 0,
            },
          })
          return
        }

        if (key === 'profiles.pending') {
          sendJson(res, 200, { message: [] })
          return
        }

        if (key === 'owner_access.access_list') {
          sendJson(res, 200, {
            message: {
              can_manage: true,
              primary_owner: 'superadmin@admin.com',
              grants: [
                {
                  user: 'tharukakarunarathne60@gmail.com',
                  enabled: 1,
                  granted_by: 'superadmin@admin.com',
                  reason: 'Platform Engineering Lead',
                },
              ],
            },
          })
          return
        }

        if (key === 'plan_catalog.list' || key === 'plan_catalog.public_plans') {
          sendJson(res, 200, {
            message: [
              { plan: 'Individual', monthly_lkr: 2500, usage_lkr: 100, storage_gb: 15 },
              { plan: 'Silver', monthly_lkr: 5000, usage_lkr: 50, storage_gb: 50 },
              { plan: 'Gold', monthly_lkr: 15000, usage_lkr: 50, storage_gb: 200 },
              { plan: 'Platinum', monthly_lkr: 22000, usage_lkr: 50, storage_gb: 500 },
            ],
          })
          return
        }

        if (key === 'private_contact.status') {
          sendJson(res, 200, {
            message: {
              phone: currentUser?.phone || '+94771234567',
              phone_verified: Boolean(currentUser?.phone_verified),
              email: currentUser?.email || '',
            },
          })
          return
        }

        if (key === 'class_keys.classroom_bank_settings' || key === 'class_keys.bank_details') {
          sendJson(res, 200, {
            message: {
              editable: true,
              owner_type: 'Institute',
              instructions: 'Bank of Ceylon — Account 0012345678 (SISU Practice Institute, Colombo 03)',
            },
          })
          return
        }

        // Safe fallback for any other read/action in local dev
        sendJson(res, 200, { message: {} })
      })
    },
  }
}
