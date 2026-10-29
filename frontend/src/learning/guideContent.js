const monthlyPricing = {
  "subtitle": "Your monthly subscription · USD",
  "body": "Your Subscription page shows your current plan, monthly price and billing dates. Class tuition is separate.",
  "formula": "Monthly total = the fixed price shown for your account.",
  "steps": [
    "Every new account receives one 14-day trial from signup. Signing in again does not restart it.",
    "Open Subscription to view your plan and monthly price. Teachers and institutes can choose View plans to see available packages.",
    "Students have one account subscription across their learning space, not a subscription for every class. Institute administrators share one institute subscription.",
    "Choose Manage under Payment details to update your invoice email or payment preference. Saving a preference does not charge you.",
    "Your invoices and receipts appear in Invoices & receipts. Download a document, then choose Print → Save as PDF for a PDF copy.",
    "Renewals follow your monthly billing anniversary. A 31 January cycle renews on the last day of February, then 31 March.",
    "Package changes during a paid period apply at renewal. Cancelling keeps your current access until its end date.",
    "Your course duration does not change the monthly SISU subscription price. Any class tuition is separate.",
    "Online payments are coming soon. Bank transfers require verified payment confirmation before access renews."
  ]
}

export const guideContent=[{...monthlyPricing,title:'How SISU pricing works',page:'subscription',icon:'Receipt',audience:'all'},{title:'Provider tools',page:'workspace',icon:'Settings2',subtitle:'Expenses, team access and content settings',body:'Gold and Platinum providers can record expenses, filter by date and export CSV; grant 2 or 5 expense-only operator seats; and configure document, protected-video and browser-session limits. Platinum adds PDF watermarks and workspace name / accent settings. Setup is required for external services.',audience:'provider'},{title:"Usage & storage",page:"storage",icon:"HardDrive",subtitle:"Keep your institute organised",body:"Institute admins can review storage use and available capacity. Remove or archive outdated material through its normal classroom controls; protect records needed for enrolled learners.",audience:"admin"},
  {
    "title": "Overview",
    "page": "dashboard",
    "icon": "LayoutDashboard",
    "subtitle": "Your starting point",
    "body": "See your classes, payments and upcoming lessons. Students can save a personal motto and exam countdown. Teachers and institutes see this month’s completed scheduled teaching hours.",
    "audience": "all"
  },
  {
    "title": "Classrooms",
    "page": "classrooms",
    "icon": "BookOpen",
    "subtitle": "Everything for one class, together",
    "body": "Choose a class by subject, grade, medium, batch year and type. Open Sessions for live lessons, Recordings for replays, Materials for PDFs/PPTs/links, Papers & assignments for assessments, and Messages for class discussions. A teacher can offer separate Sinhala and English classes for each grade.",
    "audience": "all"
  },
  {
    "title": "Schedule",
    "page": "schedule",
    "icon": "CalendarDays",
    "subtitle": "Make time for learning",
    "body": "Review scheduled lessons across your classrooms. Teachers set the date, start/end time, delivery mode and meeting link inside the classroom. A live lesson is a session within a class, not a separate course.",
    "audience": "all"
  },
  {
    "title": "Study Room",
    "page": "study",
    "icon": "Coffee",
    "subtitle": "A little space to focus",
    "body": "Choose a focus timer or stopwatch, one of 20 still colour gradients and a SISU Learning Lofi track. Adjust the music volume and pause when you need a break. Study Room is available on every package.",
    "audience": "student"
  },
  {
    "title": "Class fees",
    "page": "payments",
    "icon": "Receipt",
    "subtitle": "Pay or review class payments",
    "body": "Students choose the correct invoice, upload a bank slip and wait for approval. Reviewers verify the bank credit, inspect the student name, LMS ID, contact and submission date, then approve access or reject with a reason. A slip upload alone never unlocks a class.",
    "audience": "all"
  },
  {
    "title": "Tute delivery",
    "page": "classrooms",
    "icon": "Package",
    "subtitle": "Printed material, delivered",
    "body": "Platinum teachers can switch delivery on inside a class. Students confirm their residential address and delivery contact, then pay or submit a bank slip. The class team reviews the order and updates dispatch status.",
    "audience": "all"
  },
  {
    "title": "Teachers & institutes",
    "page": "connections",
    "icon": "Search",
    "subtitle": "Find your learning community",
    "body": "Browse verified profiles and view social links, qualifications, banners and classroom offerings. Teachers can request institute membership. An assigned teacher does not become the owner of institute tuition.",
    "audience": "all"
  },
  {
    "title": "My profile",
    "page": "profile",
    "icon": "IdCard",
    "subtitle": "Make this space yours",
    "body": "Update your profile photo, banner, description, education levels, languages and social links. Keep contact and delivery details current. Private addresses and guardian contacts are not shown on public profiles.",
    "audience": "all"
  },
  {
    "title": "News feed",
    "page": "news",
    "icon": "Newspaper",
    "subtitle": "Stay connected",
    "body": "Read class and institute updates. Approved providers can share announcements with their permitted audience. The online LMS and news feed are available on Gold and Platinum.",
    "audience": "all"
  },
  {
    "title": "WhatsApp updates",
    "page": "payments",
    "icon": "MessageCircle",
    "subtitle": "Timely updates with consent",
    "body": "Gold and Platinum providers can prepare approved message templates for payment approval and scheduled lessons. Select eligible recipients and review before sending. Delivery requires a configured WhatsApp provider, approved templates and student/guardian opt-in.",
    "audience": "provider"
  },
  {
    "title": "Wallet & payouts",
    "page": "wallet",
    "icon": "Wallet",
    "subtitle": "Your earnings and bank details",
    "body": "Add the class owner’s bank, branch, account holder and account number for finance approval. Institute tuition belongs to the institute; independent tuition belongs to the teacher. Platform-collected tuition is credited in full; SISU fees have a separate invoice. Direct bank payments already received by you are not credited again. Two payouts total per calendar month include the final-week settlement. Pending requests reserve slots; finance confirms every actual bank transfer.",
    "audience": "provider"
  },
  {
    "title": "Team & community",
    "page": "team",
    "icon": "Users",
    "subtitle": "Manage your institute",
    "body": "Review teacher membership requests, assign classroom responsibilities and manage student records. Class-level permissions control who can edit lessons, manage students or review payments. Check each teacher’s class counts and collection reports.",
    "audience": "admin"
  },
  {
    "title": "Settings & notifications",
    "page": "settings",
    "icon": "Settings",
    "subtitle": "Choose how SISU keeps you informed",
    "body": "Choose supported language, display and notification options. Review private contact preferences and consent. Product tours are available from the top bar; hover or focus help icons for field guidance.",
    "audience": "all"
  },
  {
    "title": "Provider verification",
    "page": "Verification",
    "icon": "ShieldCheck",
    "subtitle": "Review provider applications",
    "body": "Verify institute and independent teacher identities, approve profiles and provision the correct beneficiary wallet. Bank details are reviewed before use. A provider cannot approve their own destination or settle their own payout.",
    "audience": "owner"
  },
  {
    "title": "Provider billing",
    "page": "Billing",
    "icon": "Receipt",
    "subtitle": "Review monthly fees",
    ...monthlyPricing,
    "audience": "owner"
  },
  {
    "title": "Payout desk",
    "page": "Payouts",
    "icon": "Wallet",
    "subtitle": "Settle the class owner",
    "body": "Review bank destinations and queued requests. Export eligible local payouts for bank review; an export does not transfer money. Mark a transfer completed only after bank confirmation, with a unique reference. Two completed payouts per calendar month is the limit, including the monthly settlement.",
    "audience": "owner"
  },
  {
    "title": "Platform operations",
    "page": "Organizations",
    "icon": "Building2",
    "subtitle": "Operate the platform",
    "body": "Manage organization provisioning, enabled status, billing and readiness in the control plane. Tenant academic records remain on their own sites. Use the tenant owner workspace for local verification and payout review.",
    "audience": "owner"
  }
]
