// Feature presentation matches marketing/app.js. Subscription prices come only from the billing API.
const details = {
  "Individual": {
    "tier": 0,
    "description": "Start teaching online.",
    "usageRate": 100,
    "students": "30 max",
    "teachers": "1 only",
    "operators": "None",
    "highlights": [
      "Unlimited courses and exams",
      "Up to 30 students and 1 teacher",
      "Attendance and payments",
      "Zoom / YouTube / Vimeo / WhatsApp",
      "Personal learning home for Students",
      "iOS / Android apps"
    ],
    "core": [
      {
        "label": "Attendance",
        "included": true
      },
      {
        "label": "Payments",
        "included": true
      },
      {
        "label": "iOS / Android",
        "included": true
      },
      {
        "label": "Zoom / YouTube / Vimeo / WhatsApp integrations",
        "included": true
      },
      {
        "label": "Expense management",
        "included": true
      },
      {
        "label": "Personal learning home for Students",
        "included": true
      }
    ],
    "advanced": [
      {
        "label": "Limit simultaneous student logins with same credentials",
        "included": false
      },
      {
        "label": "Limit document / video views",
        "included": false
      },
      {
        "label": "Customized Secure video storage",
        "included": false
      },
      {
        "label": "Smart payment slip analysis",
        "included": false
      },
      {
        "label": "Custom domain (BYOD)",
        "included": false
      },
      {
        "label": "Student course reviews",
        "included": false
      },
      {
        "label": "Social & community",
        "included": false
      },
      {
        "label": "News Feed",
        "included": false
      },
      {
        "label": "Smart payment expiry",
        "included": false
      },
      {
        "label": "Secure Zoom meetings (coming soon)",
        "included": false
      },
      {
        "label": "Dynamic PDF watermark",
        "included": false
      },
      {
        "label": "Tute delivery",
        "included": false
      },
      {
        "label": "White label",
        "included": false
      }
    ]
  },
  "Silver": {
    "tier": 1,
    "description": "Growing classes and teams.",
    "usageRate": 50,
    "students": "Unlimited",
    "teachers": "Unlimited",
    "operators": "None",
    "highlights": [
      "Everything in Individual",
      "Unlimited students",
      "Unlimited teachers",
      "Lower fee per active student"
    ],
    "core": [
      {
        "label": "Attendance",
        "included": true
      },
      {
        "label": "Payments",
        "included": true
      },
      {
        "label": "iOS / Android",
        "included": true
      },
      {
        "label": "Zoom / YouTube / Vimeo / WhatsApp integrations",
        "included": true
      },
      {
        "label": "Expense management",
        "included": true
      },
      {
        "label": "Personal learning home for Students",
        "included": true
      }
    ],
    "advanced": [
      {
        "label": "Limit simultaneous student logins with same credentials",
        "included": false
      },
      {
        "label": "Limit document / video views",
        "included": false
      },
      {
        "label": "Customized Secure video storage",
        "included": false
      },
      {
        "label": "Smart payment slip analysis",
        "included": false
      },
      {
        "label": "Custom domain (BYOD)",
        "included": false
      },
      {
        "label": "Student course reviews",
        "included": false
      },
      {
        "label": "Social & community",
        "included": false
      },
      {
        "label": "News Feed",
        "included": false
      },
      {
        "label": "Smart payment expiry",
        "included": false
      },
      {
        "label": "Secure Zoom meetings (coming soon)",
        "included": false
      },
      {
        "label": "Dynamic PDF watermark",
        "included": false
      },
      {
        "label": "Tute delivery",
        "included": false
      },
      {
        "label": "White label",
        "included": false
      }
    ]
  },
  "Gold": {
    "tier": 2,
    "description": "Community and growth tools.",
    "usageRate": 50,
    "students": "Unlimited",
    "teachers": "Unlimited",
    "operators": "2 · Planned",
    "highlights": [
      "Everything in Silver",
      "2 operator seats (planned)",
      "News Feed, community and course reviews",
      "Customized Secure video storage and view limits",
      "Login concurrency controls",
      "Smart payment slip analysis and expiry",
      "Custom domain (BYOD)"
    ],
    "core": [
      {
        "label": "Attendance",
        "included": true
      },
      {
        "label": "Payments",
        "included": true
      },
      {
        "label": "iOS / Android",
        "included": true
      },
      {
        "label": "Zoom / YouTube / Vimeo / WhatsApp integrations",
        "included": true
      },
      {
        "label": "Expense management",
        "included": true
      },
      {
        "label": "Personal learning home for Students",
        "included": true
      }
    ],
    "advanced": [
      {
        "label": "Limit simultaneous student logins with same credentials",
        "included": true
      },
      {
        "label": "Limit document / video views",
        "included": true
      },
      {
        "label": "Customized Secure video storage",
        "included": true
      },
      {
        "label": "Smart payment slip analysis",
        "included": true
      },
      {
        "label": "Custom domain (BYOD)",
        "included": true
      },
      {
        "label": "Student course reviews",
        "included": true
      },
      {
        "label": "Social & community",
        "included": true
      },
      {
        "label": "News Feed",
        "included": true
      },
      {
        "label": "Smart payment expiry",
        "included": true
      },
      {
        "label": "Secure Zoom meetings (coming soon)",
        "included": true
      },
      {
        "label": "Dynamic PDF watermark",
        "included": false
      },
      {
        "label": "Tute delivery",
        "included": false
      },
      {
        "label": "White label",
        "included": false
      }
    ]
  },
  "Platinum": {
    "tier": 3,
    "description": "Full-service institutes.",
    "usageRate": 50,
    "students": "Unlimited",
    "teachers": "Unlimited",
    "operators": "5 · Planned",
    "highlights": [
      "Everything in Gold",
      "5 operator seats (planned)",
      "Dynamic PDF watermark",
      "Tute delivery",
      "White label"
    ],
    "core": [
      {
        "label": "Attendance",
        "included": true
      },
      {
        "label": "Payments",
        "included": true
      },
      {
        "label": "iOS / Android",
        "included": true
      },
      {
        "label": "Zoom / YouTube / Vimeo / WhatsApp integrations",
        "included": true
      },
      {
        "label": "Expense management",
        "included": true
      },
      {
        "label": "Personal learning home for Students",
        "included": true
      }
    ],
    "advanced": [
      {
        "label": "Limit simultaneous student logins with same credentials",
        "included": true
      },
      {
        "label": "Limit document / video views",
        "included": true
      },
      {
        "label": "Customized Secure video storage",
        "included": true
      },
      {
        "label": "Smart payment slip analysis",
        "included": true
      },
      {
        "label": "Custom domain (BYOD)",
        "included": true
      },
      {
        "label": "Student course reviews",
        "included": true
      },
      {
        "label": "Social & community",
        "included": true
      },
      {
        "label": "News Feed",
        "included": true
      },
      {
        "label": "Smart payment expiry",
        "included": true
      },
      {
        "label": "Secure Zoom meetings (coming soon)",
        "included": true
      },
      {
        "label": "Dynamic PDF watermark",
        "included": true
      },
      {
        "label": "Tute delivery",
        "included": true
      },
      {
        "label": "White label",
        "included": true
      }
    ]
  }
}

export const landingPlanDetails = name => details[name] || null
