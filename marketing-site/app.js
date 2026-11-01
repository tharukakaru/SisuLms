const base='';
const lms=(h='dashboard')=>`${base}/campus#${h}`;
const route=location.pathname.split('/').filter(Boolean)[0]||'home';
const page=['students','teachers','institutes','contact'].includes(route)?route:'home';
const isHome=page==='home';
const icons={tick:'<path d="m5 12.5 4.5 4.5L19 7.5"/>',down:'<path d="M12 5v14M6 13l6 6 6-6"/>',pause:'<path d="M9 5v14M15 5v14"/>',signal:'<path d="M5 19v-3M10 19v-6M15 19v-9M20 19V6"/>',battery:'<rect x="2.5" y="7" width="16" height="10" rx="2.5"/><path d="M21.5 11v2"/>',arrow:'<path d="M7 7h10v10"/><path d="M7 17 17 7"/>',book:'<path d="M4 4.5A1.5 1.5 0 0 1 5.5 3H20v15H5.5A1.5 1.5 0 0 0 4 19.5z"/><path d="M4 19.5A1.5 1.5 0 0 0 5.5 21H20"/>',clock:'<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',users:'<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20a6.5 6.5 0 0 1 13 0"/><path d="M16 4.5a3.5 3.5 0 0 1 0 7M18 14a6 6 0 0 1 3.5 6"/>',music:'<path d="M9 18V5l11-2v13"/><circle cx="6.5" cy="18" r="2.5"/><circle cx="17.5" cy="16" r="2.5"/>',palette:'<path d="M12 3a9 9 0 1 0 0 18c1.2 0 1.8-.9 1.8-1.8 0-1.3-1-1.6-1-2.7 0-1 .8-1.5 1.8-1.5H17a4 4 0 0 0 4-4C21 6.5 17 3 12 3z"/><circle cx="7.5" cy="11" r="1"/><circle cx="10" cy="7" r="1"/><circle cx="15" cy="7.5" r="1"/>',calendar:'<rect x="3.5" y="5" width="17" height="15" rx="2"/><path d="M3.5 10h17M8 3v4M16 3v4"/>',check:'<circle cx="12" cy="12" r="9"/><path d="m8 12 3 3 5-6"/>',chart:'<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>',shield:'<path d="M12 3 4.5 6v6c0 4.5 3.2 7.8 7.5 9 4.3-1.2 7.5-4.5 7.5-9V6z"/><path d="m9 12 2 2 4-4"/>',home:'<path d="M3 11 12 4l9 7"/><path d="M5 10v10h14V10"/>',spark:'<path d="M12 3v5M12 16v5M3 12h5M16 12h5M6.3 6.3l3 3M14.7 14.7l3 3M6.3 17.7l3-3M14.7 9.3l3-3"/>',video:'<rect x="3" y="6" width="13" height="12" rx="2"/><path d="m16 10 5-3v10l-5-3"/>',file:'<path d="M14 3H6.5A1.5 1.5 0 0 0 5 4.5v15A1.5 1.5 0 0 0 6.5 21h11a1.5 1.5 0 0 0 1.5-1.5V8z"/><path d="M14 3v5h5M9 13h6M9 17h6"/>',clipboard:'<rect x="5" y="4" width="14" height="17" rx="2"/><path d="M9 4V3h6v1M9 11l2 2 4-4M9 17h6"/>',wallet:'<path d="M19 7V4a1 1 0 0 0-1-1H5a2 2 0 0 0 0 4h15a1 1 0 0 1 1 1v4h-3a2 2 0 0 0 0 4h3a1 1 0 0 0 1-1v-2a1 1 0 0 0-1-1"/><path d="M3 5v14a2 2 0 0 0 2 2h15a1 1 0 0 0 1-1v-4"/>',megaphone:'<path d="M3 11v3a1 1 0 0 0 1 1h3l6 4V6L7 10H4a1 1 0 0 0-1 1z"/><path d="M17 9a4 4 0 0 1 0 6"/>',coffee:'<path d="M4 9h13v5a5 5 0 0 1-5 5H9a5 5 0 0 1-5-5z"/><path d="M17 10h1.5a2.5 2.5 0 0 1 0 5H17M8 3v3M12 3v3"/>',truck:'<path d="M3 6h11v10H3zM14 10h4l3 3v3h-7"/><circle cx="7" cy="18" r="2"/><circle cx="17.5" cy="18" r="2"/>',play:'<path d="M7 5v14l11-7z"/>',phone:'<rect x="6" y="2.5" width="12" height="19" rx="3"/><path d="M11 18.5h2"/>',heart:'<path d="M12 20s-7-4.4-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.6-7 10-7 10z"/>',globe:'<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18"/>',x:'<path d="M18 6 6 18M6 6l12 12"/>',apple:'<path d="M16 3c-1 .1-2.2.7-2.9 1.6-.6.7-1.1 1.8-1 2.9 1.1 0 2.2-.6 2.9-1.5.6-.8 1.1-1.9 1-3z"/><path d="M19 16.5c-.6 1.3-.9 1.9-1.7 3-1.1 1.6-2.2 2.5-3.4 2.5-1 0-1.4-.6-2.9-.6s-1.9.6-2.9.6c-1.2 0-2.2-1-3.3-2.6C2.6 16.4 2.4 12 4.4 9.6c.9-1.1 2.2-1.8 3.5-1.8s2.1.7 3.2.7c1 0 1.7-.7 3.2-.7 1.2 0 2.4.6 3.2 1.7-2.8 1.6-2.4 5.7.5 7z"/>',gplay:'<path d="M4 3.5v17l9-8.5z"/><path d="m4 3.5 12 7-3 2.5M4 20.5l12-7-3-2.5"/>'};
icons.search='<circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 5 5"/>';
const icon=n=>`<svg class="icon" viewBox="0 0 24 24" aria-hidden="true">${icons[n]}</svg>`;
const arrow=`<svg class="icon arr" viewBox="0 0 24 24" aria-hidden="true">${icons.arrow}</svg>`;
// Store glyphs: Simple Icons 13.21.0 (CC0), filled brand marks rather than our stroked UI icons.
const brandPaths={apple:'M12.152 6.896c-.948 0-2.415-1.078-3.96-1.04-2.04.027-3.91 1.183-4.961 3.014-2.117 3.675-.546 9.103 1.519 12.09 1.013 1.454 2.208 3.09 3.792 3.039 1.52-.065 2.09-.987 3.935-.987 1.831 0 2.35.987 3.96.948 1.637-.026 2.676-1.48 3.676-2.948 1.156-1.688 1.636-3.325 1.662-3.415-.039-.013-3.182-1.221-3.22-4.857-.026-3.04 2.48-4.494 2.597-4.559-1.429-2.09-3.623-2.324-4.39-2.376-2-.156-3.675 1.09-4.61 1.09zM15.53 3.83c.843-1.012 1.4-2.427 1.245-3.83-1.207.052-2.662.805-3.532 1.818-.78.896-1.454 2.338-1.273 3.714 1.338.104 2.715-.688 3.559-1.701',googleplay:'M22.018 13.298l-3.919 2.218-3.515-3.493 3.543-3.521 3.891 2.202a1.49 1.49 0 0 1 0 2.594zM1.337.924a1.486 1.486 0 0 0-.112.568v21.017c0 .217.045.419.124.6l11.155-11.087L1.337.924zm12.207 10.065l3.258-3.238L3.45.195a1.466 1.466 0 0 0-.946-.179l11.04 10.973zm0 2.067l-11 10.933c.298.036.612-.016.906-.183l13.324-7.54-3.23-3.21z'};
const brandIcon=n=>`<svg class="brand-ico" viewBox="0 0 24 24" aria-hidden="true"><path d="${brandPaths[n]}"/></svg>`;
let storeIconSequence=0;
const appStoreIcon=n=>n==='apple'?`<svg class="brand-ico store-color-icon" viewBox="0 0 32 32" aria-hidden="true"><defs><linearGradient id="app-store-blue-${++storeIconSequence}" x2="0" y2="1"><stop stop-color="#35c4ff"/><stop offset="1" stop-color="#0879f9"/></linearGradient></defs><rect width="32" height="32" rx="7" fill="url(#app-store-blue-${storeIconSequence})"/><g fill="none" stroke="#fff" stroke-width="2.5" stroke-linecap="round"><path d="m13 8 11 19M19 8 9 25M6 21h20"/></g></svg>`:`<svg class="brand-ico store-color-icon" viewBox="0 0 32 32" aria-hidden="true"><path fill="#32bbff" d="M5 3 18 16 5 29z"/><path fill="#00d26a" d="m5 3 17 10-4 3z"/><path fill="#ffcf00" d="m22 13 5 3-5 3-4-3z"/><path fill="#ff4b55" d="m5 29 13-13 4 3z"/></svg>`;
const logo=`<span class="logo"><img src="/marketing/assets/sisu-original-color.png" alt="sisu."></span>`;
const out=(href,label,cls='button primary')=>`<a class="${cls}" href="${href}" target="_blank" rel="noreferrer">${label}<span class="sr-only"> (opens in a new tab)</span> ${arrow}</a>`;
const demo=(label,cls='button primary')=>`<button type="button" class="${cls}" data-demo>${label} ${arrow}</button>`;
const mascot=(cls,alt='')=>`<img class="mascot ${cls}" src="/marketing/assets/mascot.png" alt="${alt}" width="500" height="500" loading="lazy" decoding="async">`;
const clip=name=>`<video class="lazy-vid" muted loop playsinline preload="none" poster="/marketing/assets/${name}.webp" aria-hidden="true"><source src="/marketing/assets/${name}.webm" type="video/webm"></video>`;
// Real LMS captures. Overview shots carry a "PREVIEW ONLY" demo bar (.crop trims it);
// modal shots sit small on a blurred page (.zoom brings the modal forward).
const barred=new Set(['sisu-teacher-overview.png','sisu-institute-overview.png','sisu-bank-payment-review.png','sisu-balanced-student-overview.png','sisu-larger-teacher-illustration.png','sisu-study-library.png']);
const modals=new Set(['sisu-unified-classroom.png','sisu-stream-schedule.png','sisu-material-delivery.png']);
const shot=(img,alt,cls='')=>`<figure class="shot${barred.has(img)?' crop':''}${modals.has(img)?' zoom':''}${cls?' '+cls:''}"><img src="/marketing/assets/${img}" alt="${alt}" loading="lazy" decoding="async"></figure>`;

const navItems=[['students','Students'],['teachers','Teachers'],['institutes','Institutes'],['contact','Contact us']];
const href=id=>isHome?`#${id}`:`/#${id}`;
const navChevron='<svg class="nav-chevron" viewBox="0 0 12 12" aria-hidden="true"><path d="m3 4.5 3 3 3-3"/></svg>';
const header=`<header class="nav-shell"><div class="nav"><a href="${isHome?'#top':'/'}" class="brand" aria-label="SISU Academy home">${logo}</a><nav id="navigation" aria-label="Main navigation"><a class="nav-platform" href="/#experience">Platform</a><a class="nav-pricing" href="/#plans">Pricing</a><a class="nav-contact" href="/contact/" ${page==='contact'?'aria-current="page"':''}>Contact</a></nav><div class="nav-end"><a class="button primary nav-cta" href="${base}/campus?signup=1">Start free trial</a><button class="menu-toggle" aria-expanded="false" aria-controls="navigation" aria-label="Open menu"><span></span><span></span></button></div></div></header>`;

/* ---------- home data (from the latest SISU build) ---------- */
const features=[
{id:'classes',label:'Classes & courses',icon:'book',kicker:'ONE CLASSROOM. ALL THE LITTLE THINGS.',title:'Give every class a proper home.',body:'Organise your teaching by subject, grade, medium, batch year and class type. Students find a teacher or institute, explore their offerings, and join the class that suits them.',bullets:['Separate classrooms for theory, revision or paper groups','A teacher profile that brings all their classes together','Institute courses with more than one teacher','Class rosters, enrolment status and teaching responsibilities'],example:'A science teacher can offer Grade 6–11 Sinhala-medium classes alongside separate English-medium groups. Each group has its own schedule, students and materials.',image:'sisu-unified-classroom.png',caption:'A selected view of the SISU classroom',plan:'Core classroom learning · all plans',route:'classrooms'},
{id:'live',label:'Live & recorded',icon:'video',kicker:'MAKE EVERY LESSON EASY TO FIND',title:'One timetable. More ways to teach.',body:'Set a lesson date, start and end time, delivery mode and joining details inside a classroom. Students see upcoming sessions across their classes in My schedule.',bullets:['Schedule YouTube, Zoom or Google Meet sessions','Embed supported YouTube lessons inside the LMS','Keep published recordings with the right classroom','Add a title and lesson context so students know what to expect'],example:'Zoom and Meet joining links can be scheduled in SISU. Watching their broadcast inside the LMS requires a configured stream relay; interactive meeting participation follows the provider’s supported joining method.',image:'sisu-stream-schedule.png',caption:'Lesson scheduling in SISU',plan:'Online lesson tools · provider setup required',route:'schedule'},
{id:'resources',label:'Materials & notes',icon:'file',kicker:'GOOD LESSONS DESERVE A GOOD HOME',title:'The notes, the links, the “save this.”',body:'Keep the supporting pieces of a lesson close to the lesson itself. Teachers can share documents, useful links and common notes with their classroom community.',bullets:['Share PDF notes and PowerPoint presentations','Keep reference links in the Materials area','Post classroom messages and shared announcements','Help enrolled students return to the right resources'],example:'After a live science lesson, share the slide deck, a revision sheet and a useful video link in the same classroom. Students do not need to search through a long chat history.',image:'sisu-unified-classroom.png',caption:'Classroom materials and messages',plan:'Online classroom resources · all plans',route:'classrooms'},
{id:'exams',label:'Exams & attendance',icon:'clipboard',kicker:'SEE THE LEARNING, NOT JUST THE LESSON',title:'A clearer picture of participation.',body:'Keep papers, assignments and attendance connected to the class. Students can submit supported assessments, while teachers review work and record participation.',bullets:['Papers and assignments inside the classroom','Student submissions and teacher marking','Attendance records for enrolled learners','Class reports to support your next teaching decision'],example:'Use a revision paper after a topic, review the submissions and check attendance before planning the next session. Teaching-hour summaries show completed scheduled time, not verified meeting attendance.',image:'sisu-teacher-overview.png',caption:'A selected teacher overview',plan:'Exams, attendance & reports · all four plans',route:'classrooms'},
{id:'payments',label:'Fees & payments',icon:'wallet',kicker:'LESS CHASING. MORE CLARITY.',title:'Know who paid, and for which class.',body:'Give each payment a clear student and invoice record. Students submit the right bank slip; your team checks the bank credit before approving access.',bullets:['Student name, LMS ID, contact and submission date','View payment proof, approve or reject with a reason','Review fees by month or a custom date range','Separate tuition records from your SISU subscription'],example:'Uploading a slip does not immediately unlock a paid class. A reviewer confirms the payment, or explains why the student needs to submit it again.',image:'sisu-bank-payment-review.png',caption:'Bank-payment reviews with student details',plan:'Payment management · all four plans · online gateway requires setup',route:'payments'},
{id:'community',label:'Community & updates',icon:'megaphone',kicker:'A CONNECTED LEARNING COMMUNITY',title:'People first. Everything else follows.',body:'Connect teacher profiles, institute pages, classrooms and updates. Students explore who teaches what; institutes bring their teaching teams and learners together.',bullets:['Profiles with qualifications, banners and social links','Teacher membership requests and class assignments','Class messages and institute news','WhatsApp templates for eligible, opted-in recipients'],example:'Prepare a class reminder or payment-approval message for eligible students. WhatsApp delivery requires provider configuration, approved templates and student or guardian consent.',image:'sisu-institute-overview.png',caption:'A selected institute workspace',plan:'Profiles & class teams · news and WhatsApp on Gold & Platinum',route:'connections'},
{id:'focus',label:'Personal study space',icon:'coffee',kicker:'A LITTLE PROGRESS, EVERY DAY',title:'Make room for a better study rhythm.',body:'Students can make their overview feel personal, set a meaningful milestone and settle into a dedicated focus space between classes.',bullets:['A personal motto and optional exam countdown','Daily learning affirmations','Focus timers, a stopwatch and study scenes','Music choices and adjustable sound volume'],example:'Choose an exam or a personal target date, then add or remove the countdown whenever you like. Dates are set by the student; they are not an official exam-calendar announcement.',image:'sisu-study-library.png',caption:'Scenes and music in the SISU study room',plan:'Study Room · all packages',route:'study'},
{id:'delivery',label:'Tute delivery',icon:'truck',kicker:'LEARNING DOESN’T ALWAYS FIT ON A SCREEN',title:'Bring printed materials into the journey.',body:'When a Platinum teacher enables delivery for a class, students can request printed tutes or other materials, confirm their details and arrange payment.',bullets:['Teacher-controlled delivery on/off setting','Residential address and delivery-contact confirmation','Payment or bank-slip submission for the order','Class-team review and dispatch-status updates'],example:'The student checks their address before submitting the order. The teacher or institute team arranges fulfilment and updates its status; SISU does not promise automatic courier dispatch.',image:'sisu-material-delivery.png',caption:'Material delivery in the classroom',plan:'Platinum only · enabled separately by the teacher',route:'classrooms'}];

const roles=[
{label:'For students',tag:'YOUR SPACE TO GROW',title:'Find your people.\nFind your potential.',copy:'Meet the teacher who makes it click. Join a class, catch a live lesson, revisit a recording and keep your materials together.',items:['Discover teachers & institutes','Live lessons, replays & materials','Your own focus space & exam countdown'],image:'sisu-balanced-student-overview.png'},
{label:'For teachers',tag:'ROOM FOR GREAT TEACHING',title:'You bring the spark.\nWe bring the space.',copy:'From your first independent class to a full teaching week. Bring your learners, lessons and everyday admin into one calm place.',items:['Classes by subject, grade & medium','Scheduling, attendance & shared notes','Payment reviews & a clearer teaching day'],image:'sisu-larger-teacher-illustration.png'},
{label:'For institutes',tag:'YOUR CAMPUS, CONNECTED',title:'Many teachers.\nOne connected campus.',copy:'Build a home for your learning community. Offer individual classes or courses taught by several teachers, with one organised student journey.',items:['Teacher profiles & a class catalogue','Courses with multiple teachers','Enrolments, fees & institute updates'],image:'sisu-institute-overview.png'}];

const starts=[
{label:'I’m a student',steps:[['Make your profile yours','Add your learning details and contact information. Set a motto or an optional exam countdown.'],['Find a teacher or institute','Explore profiles, choose a subject, grade and medium, then review the available classes.'],['Enrol and confirm payment','Select the right class invoice and submit payment or a bank slip. Wait for approval when a review is required.'],['Open your classroom','Find sessions, recordings, materials, papers and messages together. Use My schedule to plan your week.']]},
{label:'I’m a teacher',steps:[['Set up your teaching profile','Introduce your subjects, qualifications, languages and class offerings. Choose a suitable provider plan.'],['Create your classrooms','Separate grades, mediums and groups so each learner finds the right class. Connect to an institute when you teach there too.'],['Prepare your first lesson','Set the date, time and delivery mode, then add lesson materials and joining details for online sessions.'],['Welcome students and keep things moving','Review enrolments and bank slips, record attendance and share updates with your class.']]},
{label:'I run an institute',steps:[['Create your institute’s home','Add branding and profile details, choose your package and configure the services you plan to use.'],['Bring your teachers together','Review membership requests and assign teachers to the classrooms they are responsible for.'],['Organise your offerings','Publish individual classes or courses with multiple teachers. Keep subjects, groups and timetables easy to understand.'],['Run your campus from one place','Manage students, fee reviews, teaching schedules, reports and institute updates with the appropriate permissions.']]}];

const faqs=[['How do bank-slip approvals work?','Choose the correct class invoice and upload your payment proof. The reviewer sees your name, LMS ID, contact details and submission date, checks the bank credit and approves or rejects with a reason. A pending slip does not grant access to a paid class.'],['Can students watch YouTube, Zoom and Google Meet inside SISU?','Supported YouTube lessons can be embedded in the classroom. Teachers can schedule Zoom and Meet joining links. Watching a Zoom or Meet broadcast inside the LMS requires a configured stream relay; joining an interactive meeting depends on the provider’s supported method.'],['Who receives the tuition payments?','The class owner receives tuition: the institute for institute-owned classes, or the teacher for independently owned classes. Platform-collected tuition is credited in full, and SISU subscription fees are invoiced separately. Payments and transfers require activated services and finance verification.'],['How often can providers receive a payout?','The policy allows two payouts total per calendar month, including the final-week monthly settlement. Pending requests reserve a payout slot. Approved bank details and finance confirmation are required for actual transfers.'],['How does printed tute delivery work?','A Platinum teacher enables delivery for a class. Students confirm their residential address and contact details, then pay or submit a bank slip. The class team reviews the order and arranges dispatch. Delivery is optional for each class.'],['Can I send WhatsApp class and payment updates?','Every plan includes WhatsApp integration. Prepare a payment-approval or scheduled-class template, choose eligible recipients and review it before sending. Delivery requires configured services, approved templates and student or guardian opt-in.'],['Which features are still planned?','Operator accounts are planned for Gold and Platinum. Expense management and iOS and Android apps are included in every plan. PDF watermarking and white labelling are available with Platinum.'],['Is SISU only for online classes?','SISU brings your wider learning community together. Discover teachers and institutes, manage enrolments and fees, organise classroom materials and announcements, and schedule online lessons when your plan includes them.'],['Can a teacher run different classes?','Yes. A teacher can offer separate classes by grade, subject, language medium or learning group. Each classroom has its own students, schedule and materials.'],['Can an institute offer a course with several teachers?','Yes. An institute can bring several teachers and their classes together in a course, so learners have a connected place to learn.'],['How do package charges work?','Each plan has a base monthly fee plus a fee for each active student, in LKR. Individual is LKR 2,500 plus LKR 100 per active student, for up to 30 students. Silver is LKR 5,000, Gold LKR 15,000 and Platinum LKR 22,000, each plus LKR 50 per active student. An active student has made at least one payment and logged in to the LMS during the 30-day billing cycle. Every plan starts with a free trial. Class tuition is separate.'],['Where can I get the mobile app?','Explore the mobile experience using the preview on this page. App Store and Google Play links will be added here when the official download destinations are provided.'],['Can I try the LMS before choosing?','Yes. Every new account gets one 14-day trial from signup. Then subscribe monthly to continue. Signing in again does not restart the trial.']];

const lkr=n=>`LKR ${n.toLocaleString('en-US')}`;
const plans=[['Individual','Start teaching online.',2500,100,30,['Unlimited courses and exams','Up to 30 students and 1 teacher','Attendance and payments','Zoom, YouTube, Vimeo and WhatsApp','Personal learning home for students','iOS and Android apps']],['Silver','Growing classes and teams.',5000,50,0,['Everything in Individual','Unlimited students','Unlimited teachers','Lower fee per active student']],['Gold','Community and growth tools.',15000,50,0,['Everything in Silver','2 operator seats (planned)','News Feed, community and course reviews','Secure video storage and view limits','Login concurrency controls','Smart payment slip analysis and expiry','Custom domain']],['Platinum','Full-service institutes.',22000,50,0,['Everything in Gold','5 operator seats (planned)','Dynamic PDF watermark','Tute delivery','White label']]];
const activeNote='An active student has made at least one payment and logged in to the LMS during the 30-day billing cycle.';
const compareRows=[['Base monthly fee',...plans.map(p=>lkr(p[2]))],['Per active student / month',...plans.map(p=>lkr(p[3]))],['Free trial',1,1,1,1],['Courses','Unlimited','Unlimited','Unlimited','Unlimited'],['Students','Up to 30','Unlimited','Unlimited','Unlimited'],['Teachers','1','Unlimited','Unlimited','Unlimited'],['Operators','—','—','2','5'],['Exams','Unlimited','Unlimited','Unlimited','Unlimited'],['Attendance',1,1,1,1],['Payments',1,1,1,1],['iOS and Android apps',1,1,1,1],['Zoom, YouTube, Vimeo and WhatsApp integrations',1,1,1,1],['Expense management',1,1,1,1],['Personal learning home for students',1,1,1,1],['Limit simultaneous logins on one account',0,0,1,1],['Limit document and video views',0,0,1,1],['Secure video storage',0,0,1,1],['Smart payment slip analysis',0,0,1,1],['Custom domain',0,0,1,1],['Student course reviews',0,0,1,1],['Social and community',0,0,1,1],['News Feed',0,0,1,1],['Smart payment expiry',0,0,1,1],['Dynamic PDF watermark',0,0,0,1],['Tute delivery',0,0,0,1],['White label',0,0,0,1]];
const pricingGroups=[
 ['Pricing & capacity',[0,1,2,3,4,5,6,7]],
 ['Everyday learning & administration',[8,9,10,11,12,13]],
 ['Security & content controls',[14,15,16]],
 ['Payments & branding',[17,18,22,25]],
 ['Community & engagement',[19,20,21]],
 ['Specialist teaching tools',[23,24]]
];
const planFeatureValue=(row,i)=>{
 const value=compareRows[row][i+1];
 if(row===2)return '14 days';
 if(row===6&&i>1)return value+' · Planned';


 return value;
};
const cardFeatureList=i=>{
 const rows=compareRows.map((_,r)=>r).filter(r=>r>=2&&![4,5,6].includes(r));
 const item=r=>{
  const included=compareRows[r][i+1]!==0;
  const status=planFeatureValue(r,i);
  const title=r===3?'Unlimited courses':r===7?'Unlimited exams':r===2?'14-day free trial':compareRows[r][0];
  const note=included&&typeof status==='string'&&![2,3,7].includes(r)?'<small>'+status+'</small>':'';
  return '<li class="feature-'+(included?'included':'unavailable')+'" data-feature="'+r+'"><span class="feature-state" aria-label="'+(included?'Included':'Not included')+'">'+(included?'✓':'—')+'</span><span class="feature-copy">'+(included?'<strong>'+title+'</strong>':title)+note+'</span></li>';
 };
 return '<ul class="plan-feature-list plan-highlights">'+rows.slice(0,6).map(item).join('')+'</ul><details class="plan-full-features"><summary aria-label="Show or hide all plan features"><span class="see-more">See more</span><span class="see-less">See less</span><span class="expand-symbol" aria-hidden="true">+</span></summary><ul class="plan-feature-list">'+rows.slice(6).map(item).join('')+'</ul></details>';
};
const cell=v=>v===1?`<span class="yes" aria-label="Included">${icon('tick')}</span>`:v===0?'<span class="no" aria-label="Not included">—</span>':v;
const compareTable=(names,rows,caption)=>`<div class="table-scroll"><table><caption class="sr-only">${caption}</caption><thead><tr><th scope="col">Feature</th>${names.map(x=>`<th scope="col">${x}</th>`).join('')}</tr></thead><tbody>${rows.map(r=>`<tr><th scope="row">${r[0]}</th>${r.slice(1).map(v=>`<td>${cell(v)}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;

/* ---------- shared pieces ---------- */
const head=(title,sub='',cls='center')=>`<div class="head ${cls} rv"><h2>${title}</h2>${sub?`<p>${sub}</p>`:''}</div>`;
const tablist=(label,items,cls,key)=>`<div class="${cls}" role="tablist" aria-label="${label}">${items.map((t,i)=>`<button type="button" role="tab" id="${key}-tab-${i}" aria-controls="${key}-panel" aria-selected="${i===0}" tabindex="${i?-1:0}">${t}</button>`).join('')}</div>`;
const gsPanel=s=>`<ol class="steps">${s.steps.map(([h,p],i)=>`<li><span class="num">${i+1}</span><h3>${h}</h3><p>${p}</p></li>`).join('')}</ol>`;
const faqList=list=>`<div class="faq rv">${list.map(([q,a])=>`<details><summary>${q}<span class="plus" aria-hidden="true"></span></summary><p>${a}</p></details>`).join('')}</div>`;
const cta=(label='Start free trial',cls='button primary')=>out(lms('dashboard'),label,cls);
const stores=`<div class="stores"><span class="store" aria-disabled="true">${brandIcon('apple')}<span>App Store</span></span><span class="store" aria-disabled="true">${brandIcon('googleplay')}<span>Google Play</span></span></div>`;

/* Pricing cards with the same feature order for direct comparison. */
const calc=`<div class="calc-card rv" id="calc"><div class="calc-row"><label for="seats-count">Active students</label><input type="number" id="seats-count" min="0" max="2000" step="1" value="0" inputmode="numeric"></div><input type="range" id="seats" min="0" max="2000" value="0" aria-label="Active students slider" aria-valuetext="0 active students"><div class="range-ends" aria-hidden="true"><span>0</span><span id="seats-max">2,000</span></div><fieldset class="calc-plans"><legend>Plan</legend>${plans.map(([n],i)=>`<label><input type="radio" name="calc-plan" value="${i}"${i?'':' checked'}><span>${n}</span></label>`).join('')}</fieldset><p class="calc-auto" id="calc-auto" role="status"></p><p class="calc-label">Estimated monthly total</p><p class="calc-total" aria-live="polite" aria-atomic="true"><span id="calc-total">LKR 2,500</span></p><p class="calc-break" id="calc-break"></p>${out(lms('subscription'),'Start free trial','button light block')}</div>`;
const planCards=`<div class="plans snap stagger rv">${plans.map(([n,d,base,per,cap,items],i)=>`<article class="plan tier-${i}"><h3>${n}</h3><p class="price">${lkr(base)} / month<span>+ ${lkr(per)} per active student</span></p><div class="tier-card" aria-hidden="true"><span class="tc-mark">sisu<span>.</span></span><span class="tc-chip"><svg viewBox="0 0 40 30" fill="none"><rect x=".5" y=".5" width="39" height="29" rx="6"/><path d="M13 0v10H0m27-10v10h13M13 30V20H0m27 10V20h13M13 10h14v10H13z"/></svg></span><span class="tc-edition">LEARNVERSE</span><span class="tc-name">${n}</span></div><p class="plan-est" data-est="${i}"></p><dl class="rows"><div><dt>Students</dt><dd>${cap?`Up to ${cap}`:'Unlimited'}</dd></div><div><dt>Teachers</dt><dd>${i?'Unlimited':'1'}</dd></div><div><dt>Operators</dt><dd>${['None','None','2 · Planned','5 · Planned'][i]}</dd></div></dl><p class="plan-for">${d}</p>${cardFeatureList(i)}${out(lms('subscription'),`Start free trial<span class="sr-only"> on ${n}</span>`,i===3?'button light block':'button dark block')}</article>`).join('')}</div>`;

const pricingBlock=(title,sub,plansFirst=false)=>{
const calculator=`<section class="section mist" id="${plansFirst?'pricing-calculator':'plans'}"><div class="wrap split"><div class="rv"><h2>${title}</h2><p class="lead">${sub}</p><dl class="terms"><div><dt>Active student</dt><dd>${activeNote.replace('An active student has','Has')}</dd></div><div><dt>Operator</dt><dd>A team member with expense-only access.</dd></div><div><dt>Free trial</dt><dd>Every new account starts with one 14-day trial.</dd></div></dl></div>${calc}</div></section>`;
const cards=`<section class="section night"${plansFirst?' id="plans"':''}><div class="wrap">${head('Choose your plan','Base fee plus a small fee for each active student, in LKR. Use the student calculator to see your monthly total.')}${planCards}<p class="fine center-fine">Renewals follow your monthly billing date. Online payment gateways require setup. Printed delivery needs manual fulfilment and separate shipping costs.</p></div></section>`;
return plansFirst?cards+calculator:calculator+cards;
};

const marqueeItems=['Classrooms','Study Room','Lessons & notes','Assessments','Attendance','Teacher discovery','Personal schedule','Learning resources','Institute profiles','Live classrooms'];
const marquee=`<div class="marquee" aria-hidden="true"><div class="marquee-track">${[0,1].map(()=>`<div class="marquee-set">${marqueeItems.map((t,i)=>`<span>${icon(['book','coffee','file','clipboard','check','users','calendar','book','home','video'][i])}${t}</span>`).join('')}</div>`).join('')}</div></div>`;

function studyRoom(){return `<section class="section night study-sec" id="study-room"><div class="wrap split"><div class="rv pocket low"><img class="pocket-art" src="/marketing/assets/study.png" alt="" width="499" height="499" loading="lazy" decoding="async" aria-hidden="true"><p class="feature-label">Study Room · Included in every plan</p><h2>A little breathing room.<br><span class="accent-text">A lot more focus.</span></h2><p class="lead">The Study Room gives every student a focus timer, a stopwatch and breaks, with 20 gradients and 21 lo-fi tracks. It is included in every plan.</p>${cta('Open the Study Room','button light')}</div><figure class="media reveal rv"><video autoplay muted loop playsinline controls preload="metadata" aria-label="Silent recording of the SISU Study Room"><source src="/marketing/assets/sisu-focus.webm" type="video/webm"><source src="/marketing/assets/sisu-focus.mp4" type="video/mp4"></video></figure></div></section>`}

/* ---------- home ---------- */
// One real LMS screen per feature; materials share the classroom capture, so they ride with "classes".
const tiles=[{label:'Teacher workspace',icon:'users',title:'One teacher. Many possibilities.',body:'A Grade 8 class is different from an O/L revision group. Your independent classrooms and institute assignments stay clearly organised in one workspace.',video:'sisu-teacher-workspace.mp4',image:'sisu-teacher-workspace.webp',caption:'Five-second screen recording of the SISU teacher dashboard, showing the overview and teaching schedule. Demonstration data.',plan:'Recorded in SISU · 5-second preview',teacher:true},...features.filter(f=>f.id!=='resources'),{label:'Student home',icon:'home',title:'A personal learning home.',body:'Each student gets an overview with today’s lessons, a calendar, an exam countdown and a personal motto, so every day starts in one place.',image:'sisu-balanced-student-overview.png',caption:'A student overview in the SISU LMS',plan:'Personal learning home · all plans'}];
const teacherBenefits=`<div class="points teacher-benefits">${[['book','A classroom for every group','Separate classrooms by grade, medium, batch and class type.'],['users','Independent and institute teaching','Your own classes and institute assignments stay clearly apart.'],['calendar','One teaching schedule','Sessions from every class in a single calendar.'],['wallet','Fees by class','Each class keeps its own invoices and slip reviews.']].map(([i,h,p])=>`<div>${icon(i)}<h3>${h}</h3><p>${p}</p></div>`).join('')}</div>`;
const exPanel=f=>`${f.video?`<figure class="workspace-recording"><video controls muted loop playsinline preload="metadata" poster="/marketing/assets/${f.image}" aria-label="${f.caption}"><source src="/marketing/assets/${f.video}" type="video/mp4">Your browser does not support this video.</video></figure>`:shot(f.image,f.caption)}<div class="ex-copy"><h3>${f.title}</h3><p>${f.body}</p><p class="note">${f.plan}</p></div>${f.teacher?teacherBenefits:""}`;
const socialFeatures=[['search','Find teachers','Search for teachers by name, subject or grade. Find the right fit for your learning.'],['users','Teacher profiles','Get to know teachers through their qualifications, subjects and available classes.'],['globe','Social links','Teachers can add their social profiles, so students can explore more of what they share.'],['megaphone','Follow updates','Follow teachers and institutes to stay connected with their news and class updates.'],['book','Join classes','Turn a new connection into learning. Join classes and keep lessons and resources together.']];

const orb=(n,cls)=>`<img class="orb ${cls}" src="/marketing/assets/element/part-${n}.png" alt="" loading="lazy" decoding="async">`;
const orbsMarkup=`<div class="orbs tl rv" aria-hidden="true">${orb(1,'a')}${orb(5,'b')}${orb(6,'c')}${orb(7,'d')}${orb(4,'e')}${orb(3,'f')}</div><div class="orbs br rv" aria-hidden="true">${orb(2,'a')}${orb(3,'b')}${orb(5,'c')}${orb(4,'d')}${orb(6,'e')}</div>`;

/* ---------- intro video + voices (edit these two lists; nothing else needs to change) ---------- */
// Swap in the real SISU video here. hasAudio:true shows the Unmute control; captions takes a .vtt path.
const introVideo={src:'/marketing/assets/learnverse-world.mp4',type:'video/mp4',poster:'/marketing/assets/learnverse-world-hd-small.webp',label:'A look inside the SISU learning world',hasAudio:false,captions:''};
// shortcut: these are labelled sample quotes; replace with real, permissioned quotes (sample:false) before launch.
const voices=[
  {
    "name": "Student",
    "role": "Learning with SISU",
    "lang": "en",
    "face": 0,
    "quote": "My classes, recordings and notes are finally in one place. I can spend more time learning and less time looking for the right lesson.",
    "sample": true
  },
  {
    "name": "Teacher",
    "role": "Independent tutor",
    "lang": "si",
    "face": 1,
    "quote": "මගේ පන්ති, පාඩම් සහ ගෙවීම් එකම තැනකින් බලන්න පුළුවන්. ඒ නිසා සිසුන්ට උගන්වන්න වැඩි කාලයක් වෙන් කරන්න මට පහසුයි.",
    "sample": true
  },
  {
    "name": "Teacher",
    "role": "Blended learning",
    "lang": "en",
    "face": 2,
    "quote": "I can keep my classroom lessons and online resources together. My students know where to find their notes and what to prepare for next.",
    "sample": true
  },
  {
    "name": "Student",
    "role": "Personal study space",
    "lang": "si",
    "face": 3,
    "quote": "Study Room එකේ කාල ගණකය මට අවධානයෙන් පාඩම් කරන්න උදව් වෙනවා. මගේ විභාග ඉලක්කයත් හැමදාම මතක් වෙන නිසා ඉදිරියට යන්න හිතෙනවා.",
    "sample": true
  },
  {
    "name": "Institute",
    "role": "Institute administrator",
    "lang": "en",
    "face": 4,
    "quote": "Having our teachers, classes and schedules in one place makes the day easier to organise. Our team can find the information they need quickly.",
    "sample": true
  },
  {
    "name": "Student",
    "role": "Learning community",
    "lang": "si",
    "face": 5,
    "quote": "මට ගැළපෙන ගුරුවරයෙක් හොයාගෙන පන්තියකට සම්බන්ධ වෙන්න පහසුයි. පාඩම් සටහන් සහ පටිගත කළ පාඩම් එකම තැනක තියෙන එක ගොඩක් ප්‍රයෝජනවත්.",
    "sample": true
  },
  {
    "name": "Teacher",
    "role": "Teaching community",
    "lang": "en",
    "face": 6,
    "quote": "My profile brings my classes and social links together. Students can get to know how I teach before choosing a class that suits them.",
    "sample": true
  },
  {
    "name": "Institute",
    "role": "Connected classrooms",
    "lang": "si",
    "face": 7,
    "quote": "අපේ ගුරුවරුන්ගේ පන්ති සහ කාලසටහන් එකම තැනකින් සංවිධානය කරන්න පුළුවන්. සිසුන්ටත් තමන්ගේ ඊළඟ පාඩම හොයාගන්න පහසුයි.",
    "sample": true
  }
];
const playIcon='<svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M8 5.5v13l11-6.5z" fill="currentColor" stroke="none"/></svg>',pauseIcon='<svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M8 5h3v14H8zM13 5h3v14h-3z" fill="currentColor" stroke="none"/></svg>';
const videoSection=`<section class="section vid-sec" id="video"><div class="wrap"><div class="vplayer rv" data-state="idle"><video class="vp-video" muted playsinline loop preload="none" poster="${introVideo.poster}" aria-label="${introVideo.label}"><source src="${introVideo.src}" type="${introVideo.type}">${introVideo.captions?`<track kind="captions" srclang="en" label="English" src="${introVideo.captions}" default>`:''}</video>${introVideo.hasAudio?'<button type="button" class="vp-unmute">Unmute</button>':''}<button type="button" class="vp-toggle" aria-label="Play video">${playIcon}</button><div class="vp-bar"><input type="range" class="vp-seek" min="0" max="1000" value="0" step="1" aria-label="Seek video"><span class="vp-time" aria-hidden="true">0:00</span>${introVideo.hasAudio?'<button type="button" class="vp-mute" aria-label="Unmute video">'+icon('music')+'</button>':''}<button type="button" class="vp-full" aria-label="Full screen">${icon('arrow')}</button></div></div></div></section>`;
const voicesSection=`<section class="section voices" id="voices" aria-label="Testimonials"><div class="wrap">${head('Loved by the people<br>learning and teaching on SISU')}<div class="voice-carousel" aria-roledescription="carousel" aria-label="Sinhala and English sample testimonials"><ul class="voice-track" id="voice-track" tabindex="0" aria-label="Swipe or use the arrow keys to browse testimonials">${voices.map((v,i)=>`<li class="voice" aria-label="${i+1} of ${voices.length}"><div class="voice-who"><span class="voice-avatar voice-portrait" aria-hidden="true" style="background-position:${(v.face%4)*100/3}% ${Math.floor(v.face/4)*100}%"></span><span><strong>${v.name}</strong><small>${v.role}</small></span>${v.sample?'<em class="voice-sample">Sample</em>':''}</div><blockquote><p lang="${v.lang}">${v.quote}</p></blockquote></li>`).join('')}</ul></div><div class="voice-cta rv">${cta('Start your 14-day trial','button voice-trial')}</div></div></section>`;
const home=()=>`<section class="hero hero-photo" id="top"><div class="hero-media"><picture><source media="(max-width: 1100px)" srcset="/marketing/assets/learnverse-student-640.webp 640w, /marketing/assets/learnverse-student-960.webp 960w, /marketing/assets/learnverse-student-1280.webp 1280w" sizes="100vw"><img class="hero-image" src="/marketing/assets/learnverse-student-1672.webp" srcset="/marketing/assets/learnverse-student-960.webp 960w, /marketing/assets/learnverse-student-1280.webp 1280w, /marketing/assets/learnverse-student-1672.webp 1672w" sizes="(max-width: 1100px) 100vw, (min-width: 1770px) 1380px, 78vw" width="1672" height="941" alt="A student exploring the SISU learning dashboard on her laptop." loading="eager" fetchpriority="high" decoding="async"></picture></div><div class="wrap hero-content"><p class="feature-label load">SISU Academy introduces</p><h1 class="hero-mark"><span class="ln"><span>LearnVerse</span></span></h1><p class="hero-descriptor load" style="--d:.2s">The smart learning management<br><span>social platform.</span></p><div class="hero-row load" style="--d:.35s"><p>A whole learning universe in one place: discover teachers, join classes, learn together and keep growing between lessons.</p><div class="actions"><div class="app-download" role="group" aria-label="Download the SISU app"><div class="app-download-heading">${icon('phone')}<span>Download the SISU app</span></div><div class="app-download-stores"><span class="app-download-store" aria-disabled="true">${appStoreIcon('apple')}<span>App Store</span></span><span class="app-download-store" aria-disabled="true">${appStoreIcon('googleplay')}<span>Google Play</span></span></div></div></div></div></div>${marquee}</section>

<section class="section mist orbit" id="experience">${orbsMarkup}<div class="wrap">${head('Find your teachers.<br>Build your learning community.','Search for teachers, explore their profiles and social links, and stay connected to classes and updates — all in LearnVerse.')}<ul class="stats social-features stagger rv">${socialFeatures.map(([i,title,copy])=>`<li>${icon(i)}<h3>${title}</h3><p>${copy}</p></li>`).join('')}</ul></div></section>

<section class="section discover-section" id="community" aria-labelledby="discover-title"><div class="wrap"><div class="discover-heading rv"><span class="discover-pill">Discover LearnVerse</span><h2 id="discover-title">A whole world of learning.<br>Made for your everyday.</h2><p>Find the right people. Learn online and in the classroom. Bring your learning community together — all in one connected space.</p></div><div class="discover-grid"><article class="discover-card rv"><a class="discover-card-link" href="/students/" aria-label="Discover your next teacher."><div class="discover-photo story-discover"><img src="/marketing/assets/learnverse-final-discover-960.webp" srcset="/marketing/assets/learnverse-final-discover-480.webp 480w, /marketing/assets/learnverse-final-discover-960.webp 960w, /marketing/assets/learnverse-final-discover-1448.webp 1448w" sizes="(max-width: 700px) calc(100vw - 40px), (max-width: 1320px) calc((100vw - 112px) / 2), 604px" width="1448" height="1086" alt="Three Sri Lankan teachers in saree, osari and smart-casual clothing." loading="lazy" decoding="async"><div class="teacher-search-preview" aria-hidden="true">${icon('search')}<span>Search teachers, subjects or grades</span><span class="teacher-search-filter"><svg viewBox="0 0 24 24"><path d="M4 7h16M4 17h16M9 4v6M15 14v6"/></svg></span></div><div class="story-panel" aria-hidden="true"><div class="story-panel-label"><span class="story-panel-icon">${icon('search')}</span><span>Find your teacher<small>Discover a new connection</small></span></div><div class="story-tags"><span>Subjects</span><span>Grades</span><span>Social profiles</span></div></div></div><div class="discover-card-heading"><h3>Discover your next teacher.</h3>${icon('arrow')}</div></a><p>Find teachers by subject or grade. Explore their profiles, qualifications and social links, then choose a class that feels right for you.</p></article><article class="discover-card rv"><a class="discover-card-link" href="/students/" aria-label="Learn better, together."><div class="discover-photo story-learn"><img src="/marketing/assets/learnverse-final-learn-960.webp" srcset="/marketing/assets/learnverse-final-learn-480.webp 480w, /marketing/assets/learnverse-final-learn-960.webp 960w, /marketing/assets/learnverse-final-learn-1448.webp 1448w" sizes="(max-width: 700px) calc(100vw - 40px), (max-width: 1320px) calc((100vw - 112px) / 2), 604px" width="1448" height="1086" alt="Sri Lankan students collaborating with a laptop and study notes." loading="lazy" decoding="async"><div class="story-panel" aria-hidden="true"><div class="story-panel-label"><span class="story-panel-icon">${icon('users')}</span><span>Your learning community<small>A place to connect and grow</small></span></div><div class="story-tags"><span>Classes</span><span>Resources</span><span>Updates</span></div></div></div><div class="discover-card-heading"><h3>Learn better, together.</h3>${icon('arrow')}</div></a><p>Join a class and become part of a learning community. Connect classroom learning with online lessons, shared notes and conversations.</p></article><article class="discover-card rv"><a class="discover-card-link" href="/teachers/" aria-label="Share what you know."><div class="discover-photo story-teach"><img src="/marketing/assets/learnverse-final-teach-960.webp" srcset="/marketing/assets/learnverse-final-teach-480.webp 480w, /marketing/assets/learnverse-final-teach-960.webp 960w, /marketing/assets/learnverse-final-teach-1448.webp 1448w" sizes="(max-width: 700px) calc(100vw - 40px), (max-width: 1320px) calc((100vw - 112px) / 2), 604px" width="1448" height="1086" alt="A Sri Lankan teacher in an osari preparing lessons with a laptop and notebook." loading="lazy" decoding="async"><div class="teacher-social-preview" aria-hidden="true"><span class="social-bubble facebook"><svg viewBox="0 0 24 24"><path d="M14 21v-8h3l.5-4H14V7c0-1 .4-1.5 1.7-1.5H18V2.2c-.7-.1-1.8-.2-3-.2-3 0-5 1.8-5 5v2H7v4h3v8z"/></svg></span><span class="social-bubble youtube"><svg viewBox="0 0 24 24"><rect x="2" y="5" width="20" height="14" rx="4"/><path d="m10 9 6 3-6 3z" fill="white"/></svg></span><span class="social-bubble instagram"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.5" cy="6.5" r="1" fill="currentColor" stroke="none"/></svg></span></div><div class="story-panel" aria-hidden="true"><div class="story-panel-label"><span class="story-panel-icon">${icon('globe')}</span><span>Your teaching profile<small>Your expertise. Your community.</small></span></div><div class="story-tags"><span>Profile</span><span>Social links</span><span>Classes</span></div></div></div><div class="discover-card-heading"><h3>Share what you know.</h3>${icon('arrow')}</div></a><p>Build your teaching profile, add your social links and help students discover you. Bring your classes, learners and everyday teaching into one place.</p></article><article class="discover-card rv"><a class="discover-card-link" href="/institutes/" aria-label="Bring your institute together."><div class="discover-photo story-manage"><img src="/marketing/assets/learnverse-final-manage-960.webp" srcset="/marketing/assets/learnverse-final-manage-480.webp 480w, /marketing/assets/learnverse-final-manage-960.webp 960w, /marketing/assets/learnverse-final-manage-1448.webp 1448w" sizes="(max-width: 700px) calc(100vw - 40px), (max-width: 1320px) calc((100vw - 112px) / 2), 604px" width="1448" height="1086" alt="A Sri Lankan teacher leading an in-person class with remote learners joining online." loading="lazy" decoding="async"><div class="story-panel" aria-hidden="true"><div class="story-panel-label"><span class="story-panel-icon">${icon('home')}</span><span>One connected institute<small>People and classrooms, together</small></span></div><div class="story-tags"><span>In person</span><span>Online</span><span>Connected</span></div></div></div><div class="discover-card-heading"><h3>Bring your institute together.</h3>${icon('arrow')}</div></a><p>Bring in-person and online classes together. Connect your teachers and students, and organise schedules, enrolments and institute updates from one learning home.</p></article></div></div></section>








<section class="section mist pay-bg" id="how-payments-work"><div class="wrap">${head('Clear for your students.<br>Clear for your team.','Class fees, payment reviews and provider billing have different jobs. Here is how they fit together.')}<ol class="steps three stagger rv">${[['Choose a class','The student selects a teacher or institute’s class, enrols and receives the relevant invoice.'],['Submit the payment','Pay through an activated gateway or upload a bank slip against the correct invoice.'],['Confirm and learn','The class team verifies a bank payment before approving access. Rejections include a reason.']].map(([h,p],i)=>`<li><span class="num">${i+1}</span><h3>${h}</h3><p>${p}</p></li>`).join('')}</ol><div class="split pay"><div class="rv"><h3 class="h3l">Tuition belongs to the class owner.</h3><p>Institute-owned tuition goes to the institute. Independent class tuition goes to the teacher. Platform-collected tuition is credited in full, with SISU plan charges billed separately.</p><ul class="ticks"><li>Bank, branch, account holder and account number go through finance approval.</li><li>Two payouts per calendar month, including the final-week settlement.</li><li>Direct bank payments already received by the owner are not credited to the platform wallet again.</li><li>Online collections and transfers depend on activated payment services.</li></ul></div><div class="reveal rv">${shot('sunlit-teacher-workspace.png','A teacher using the SISU dashboard in a sunlit home workspace','payment-workspace')}</div></div></div></section>

<section class="section learner-experience" id="student-experience" aria-labelledby="learner-title"><div class="wrap"><div class="learner-heading rv"><span class="mobile-kicker">Made around you</span><h2 id="learner-title">A <span>learner-centred</span><br>student experience.</h2><p class="lead">Turn everyday screen time into time for learning. A personal space to see your goals, build a study rhythm and feel encouraged along the way.</p></div><div class="learner-overview"><figure class="learner-art rv"><img src="/marketing/assets/student-learning-together.png" width="1024" height="1536" loading="lazy" decoding="async" alt="A student seated with the SISU mascot, presenting his learning dashboard on a laptop."></figure><div class="learner-tools rv"><div class="learner-benefits learner-purpose">${[
['calendar','Your exam goal, always in sight','Set your exam target date and personal countdown. Keep the next milestone close, with a daily motto that makes it yours.'],
['heart','A little encouragement, every day','Daily learning affirmations offer a positive thought to return to. A reminder that your effort matters, one small step at a time.'],
['clock','Make time work for you','Use the Study Room to plan focused sessions, track your time and take breaks. Build a study rhythm that fits your day.'],
['palette','A learning space that feels like yours','Your classes, your goals and your own pace. Personal themes and a welcoming learning home put you at the centre.'],
['phone','Keep your next class close','Receive WhatsApp class-schedule reminders when your learning team enables the service and you opt in. Keep your timetable within reach.']
].map(([i,h,p])=>`<div>${icon(i)}<div><h3>${h}</h3><p>${p}</p></div></div>`).join('')}</div><p class="learner-notification-note">Coming to the mobile app: daily affirmation notifications. WhatsApp reminders require activated services and student or guardian opt-in.</p></div></div><div class="learner-journey-heading rv"><h3>Everything a student can do.<br><span>In one place.</span></h3><p>From finding your teacher to revising on your own, every step stays connected.</p></div><div class="learner-journey">${[
['Discover & enrol',[['search','Find your teachers','Explore teachers, institutes and classes by subject, grade and medium.'],['users','Follow, join, enrol','Follow updates, request membership and enrol in the class that fits.'],['globe','One learner, many providers','One account across your teachers and institutes, each with its own class fees.']]],
['Learn in class',[['book','Your classrooms','Find your classes by type, medium or grade, with lessons and resources together.'],['video','Live lessons & replays','Join the right lesson or catch up with recordings shared by your teacher.'],['clipboard','Papers & feedback','Complete timed attempts, submit PDF answers where allowed, and see marks and comments.']]],
['Plan & focus',[['calendar','Your schedule','Keep a monthly lesson calendar, with Google Calendar sync when connected.'],['chart','Your exam countdown','Choose your goal, target date and daily motto on your personal overview.'],['coffee','Your Study Room','Focus with a timer, stopwatch, breaks, calming gradients and lo-fi music.']]],
['Pay & stay connected',[['wallet','Class fees','Pay by bank transfer, upload your slip and follow its review status.'],['truck','Printed tutes','Order printed notes and follow their delivery through to dispatch.'],['megaphone','Your feed & reminders','Follow class news and updates, with WhatsApp schedule reminders when enabled and opted in.']]]
].map(([title,items],i)=>`<div class="learner-stage rv"><div class="learner-stage-title"><span>0${i+1}</span><h4>${title}</h4></div>${items.map(([ic,h,p])=>`<article>${icon(ic)}<h5>${h}</h5><p>${p}</p></article>`).join('')}</div>`).join('')}</div></div></section>



<section class="section bg-video" id="getting-started"><div class="section-bg" aria-hidden="true"><video class="lazy-vid" muted loop playsinline preload="none" poster="/marketing/assets/BG2.jpg"><source src="/marketing/assets/BG2.mp4" type="video/mp4"></video></div><div class="wrap">${head('From hello to your first lesson','New to SISU? Choose your role. Here is a practical place to begin.')}${tablist('Choose your role',starts.map(s=>s.label),'role-tabs rv','gs')}<div id="gs-panel" class="rv" role="tabpanel" aria-labelledby="gs-tab-0">${gsPanel(starts[0])}</div></div></section>

${pricingBlock('Pay for the students who learn.','A base monthly fee, plus a small fee only for students who are active that month. Pick a plan, move the slider, and see your total.',true)}

${voicesSection}

<section class="section mist" id="faq"><div class="wrap split top"><div class="rv"><h2>Questions,<br>answered.</h2><p class="lead">Here are a few things you might be wondering.</p><figure class="faq-art"><video class="lazy-vid" muted loop playsinline preload="none" poster="/marketing/assets/girl-stop-poster.jpg" width="736" height="1120" aria-hidden="true"><source src="/marketing/assets/girl-stop.mp4" type="video/mp4"></video></figure></div>${faqList(faqs)}</div></section>
${closing}

<section class="section mobile-section" id="mobile"><div class="wrap split"><div class="rv mobile-copy"><span class="mobile-kicker">Get the SISU app</span><h2>Your classroom,<br>in your pocket.</h2><p class="lead">The SISU mobile app brings your schedule, lessons and class news with you. iOS and Android apps are included in every plan.</p><div class="stores mobile-stores"><span class="store" aria-disabled="true">${appStoreIcon('apple')}<span>App Store</span></span><span class="store" aria-disabled="true">${appStoreIcon('googleplay')}<span>Google Play</span></span></div></div><figure class="mobile-mockup rv"><img class="mobile-creative" src="/marketing/assets/sisu-three-phones.png" width="1536" height="1024" loading="lazy" decoding="async" alt="Three SISU smartphones showing the teacher dashboard, student home and classrooms."></figure></div></section>`;

/* ---------- secondary pages (previous build routes) ---------- */
const data={students:{title:'Your curiosity.',italic:'Your kind of classroom.',copy:'Find your teachers, keep your learning together and make a little progress, every day.',img:'white-focus.webp',shot:['sisu-balanced-student-overview.png','A student overview in the SISU LMS'],features:[['Your classrooms, together','Lessons, notes, resources and announcements in one home for each subject.'],['Make space for focus','Settle into the Study Room with a focus timer, stopwatch, breaks, 20 pastel gradients and 21 lo-fi tracks.'],['Keep moving forward','Follow your schedule, submit assessments and see the feedback that helps you grow.']],steps:[['Sign in with Google','Use your Google account to begin your SISU journey.'],['Make it yours','Complete your profile and required verification.'],['Find your classroom','Discover teachers and institutes, request access and join your permitted classes.']]},teachers:{title:'You bring the spark.',italic:'We bring the space.',copy:'A thoughtful teaching home for your classes, your knowledge and the community you build around them.',img:'white-classrooms.webp',shot:['sisu-larger-teacher-illustration.png','A teacher overview in the SISU LMS'],features:[['Teach in your own rhythm','Organise classes, schedule lessons and bring your resources together.'],['See the next step','Create assessments, review submissions and keep attendance records.'],['Build real connections','Create your teaching profile and help learners find their place with you.']],steps:[['Tell us about yourself','Apply as an individual Teacher and verify your email.'],['Complete your profile','After application approval, complete required verification and your teaching profile.'],['Build your teaching home','Once your profile is approved, organise your classes and welcome your learners.']]},institutes:{title:'Many bright minds.',italic:'One connected home.',copy:'Give your teachers, students and team a shared space to do their best work, with a clear view of the everyday.',img:'white-community.webp',shot:['sisu-institute-overview.png','An institute overview in the SISU LMS'],features:[['Bring your team together','Manage your institute workspace, people and classrooms with role-based access.'],['Keep the details in view','Organise teaching schedules, attendance and operational records.'],['Make your identity visible','Create an institute profile and a connected home for your learning community.']],steps:[['Introduce your institute','Submit your provider application and verify your email.'],['Complete verification','Finish the required phone and profile steps, followed by platform review.'],['Connect your people','Set up your institute workspace, teachers and classrooms after approval.']]}};
const featureIcons=['book','clock','chart'];
const roleFaqs=[['Is the trial a free plan?','Your trial lasts 14 days. It is not a permanent free subscription, and signing in again does not restart it.'],['Does my subscription include class tuition?','No. Your SISU subscription and any tuition charged by a teacher or institute are separate.'],['Can I attend a live lesson?','Authorised learners can join a started LiveKit classroom. Recordings are available only after the teacher has reviewed and published them.'],['Which services are available now?','Core staging learning flows have been tested. SMS, WhatsApp and online payments remain deferred. Public onboarding and some connected services still need configuration and acceptance testing.']];
const studentFees=`<section class="section mist" id="plans"><div class="wrap split"><div class="rv"><h2>How fees work<br>for students</h2><ul class="ticks lg"><li>Your teacher or institute sets each class fee</li><li>Pay against an invoice or upload a bank slip</li><li>Follow every payment until it is approved</li></ul></div><div class="calc-card rv"><h3>SISU Student</h3><p>Join a class to open your classroom, Study Room, schedule and mobile app.</p>${cta('Start free trial','button light block')}<p class="calc-fine">Class tuition is set by and paid to the class owner. Online payments are not yet enabled.</p></div></div></section>`;
function rolePage(){const d=data[page];return `<section class="page-hero"><div class="wrap head center"><h1 class="hero-title"><span class="ln"><span>${d.title}</span></span><span class="ln"><span>${d.italic}</span></span></h1><p class="load" style="--d:.4s">${d.copy}</p><div class="actions load" style="--d:.55s">${cta('Start free trial','button dark')}<a class="button ghost-dark" href="#plans">Explore plans</a></div></div><div class="wrap load" style="--d:.7s">${shot(...d.shot)}</div></section>
<section class="section mist"><div class="wrap split"><div class="rv"><h2>What you can do<br>with SISU</h2><div class="points one">${d.features.map(([h,p],i)=>`<div>${icon(featureIcons[i])}<h3>${h}</h3><p>${p}</p></div>`).join('')}</div></div><figure class="media reveal rv"><img src="/marketing/assets/${d.img}" alt="Illustration of a connected learning space" loading="lazy"></figure></div></section>${page==='students'?studyRoom()+studentFees:pricingBlock('Pay for the students who learn.','A base monthly fee, plus a small fee only for students who are active that month. Pick a plan, move the slider, and see your total.')}
<section class="section"><div class="wrap">${head('Your first steps')}<ol class="steps three stagger rv">${d.steps.map(([h,p],i)=>`<li><span class="num">${i+1}</span><h3>${h}</h3><p>${p}</p></li>`).join('')}</ol><div class="notice rv">${icon('shield')}<p><strong>A note before you begin.</strong> Staging is open for existing test accounts. ${page==='students'?'New profile completion needs phone verification, which is not enabled yet.':'Public provider applications are currently closed pending the published privacy policy; phone verification is also pending.'} The trial button opens the staging sign-in page.</p></div></div></section>
<section class="section mist"><div class="wrap split top"><div class="rv"><h2>Good<br>questions.</h2></div>${faqList(roleFaqs)}</div></section>`;}
function contact(){return `<section class="page-hero short"><div class="wrap head center"><h1 class="hero-title"><span class="ln"><span>A good conversation.</span></span><span class="ln"><span>A brighter beginning.</span></span></h1><p class="load" style="--d:.4s">Have a question about learning, teaching or bringing your institute to SISU? Start here.</p></div></section><section class="section mist"><div class="wrap split top"><div class="rv"><h2>What’s on<br>your mind?</h2><p class="lead">Tell us a little about yourself and what you're looking for.</p><div class="points one"><div>${icon('home')}<h3>Already part of a classroom?</h3><p>For class-specific questions, contact your teacher or institute through your learning space.</p>${out(lms('dashboard'),'Open your LMS','text-link')}</div></div></div><form id="contact-form" class="form rv"><div class="form-row"><label>Your name<input name="name" required autocomplete="name" placeholder="Your full name"></label><label>Email address<input name="email" type="email" required autocomplete="email" placeholder="you@example.com"></label></div><label>WhatsApp number <span class="fine">(optional)</span><input name="whatsapp" type="tel" autocomplete="tel" inputmode="tel" placeholder="+94 77 123 4567" maxlength="30"></label><label>I’m here as<select name="role"><option>A student</option><option>A teacher</option><option>An institute</option><option>Someone curious</option></select></label><label>How can we help?<textarea name="message" rows="5" required placeholder="Tell us a little about what you have in mind"></textarea></label><p class="fine">Design preview: enquiries aren't sent yet. You can save your message below; a contact destination will be connected before launch.</p><button class="button dark" type="submit">Save enquiry draft ${arrow}</button><p id="form-status" role="status"></p></form></div></section>`;}

/* ---------- shared closing, footer, dialog ---------- */
const closing=`<section class="closing"><video class="closing-bg lazy-vid" muted loop playsinline preload="none" poster="/marketing/assets/learnverse-world-hd-small.webp" aria-hidden="true"><source src="/marketing/assets/learnverse-world.mp4" type="video/mp4"></video><div class="wrap closing-inner rv"><div class="glass">${mascot('sisu-peek')}<h2>Bring your <span class="curiosity-accent">curiosity</span>.<br>We’ll make room for it.</h2><p>Every new account starts with a 14-day trial.</p>${demo('Come on in','button light')}</div></div></section>`;
const footerSocialAccounts = [
 {name:'Facebook',url:null,art:'<path d="M14 22v-9h3l.5-4H14V7c0-1.2.3-2 2-2h2V1.4A25 25 0 0 0 15 1c-3 0-5 1.8-5 5v3H7v4h3v9z"/>'},
 {name:'Instagram',url:null,art:'<rect x="3" y="3" width="18" height="18" rx="5" fill="none" stroke="currentColor" stroke-width="1.8"/><circle cx="12" cy="12" r="4" fill="none" stroke="currentColor" stroke-width="1.8"/><circle cx="17.5" cy="6.5" r="1.2"/>'},
 {name:'TikTok',url:null,art:'<path d="M14 2h3c.3 2.7 1.8 4.3 4.5 4.5v3.2a10 10 0 0 1-4.5-1.5V16a6 6 0 1 1-6.5-6v3.2a2.8 2.8 0 1 0 3.5 2.7z"/>'},
 {name:'LinkedIn',url:null,art:'<path d="M4 8h4v13H4zM10 8h3.8v1.8c.8-1.3 2-2.1 3.7-2.1 3 0 4.5 1.8 4.5 5.4V21h-4v-7c0-1.8-.4-2.8-1.9-2.8-1.6 0-2.1 1.2-2.1 2.8v7h-4z"/><circle cx="6" cy="4" r="2.2"/>'}
];
const footerSocial = '<div class="ft-socials" role="group" aria-label="SISU social media">'+footerSocialAccounts.map(({name,url,art})=>{const graphic='<svg viewBox="0 0 24 24" aria-hidden="true">'+art+'</svg>';return url?'<a href="'+url+'" target="_blank" rel="noopener noreferrer" aria-label="SISU on '+name+'">'+graphic+'</a>':'<span role="link" aria-disabled="true" aria-label="'+name+' — link to be added" title="'+name+' — link to be added">'+graphic+'</span>';}).join('')+'</div>';
const footer=`${isHome?'':closing}<footer class="site-footer"><div class="wrap"><div class="ft-top"><p class="ft-tag">A little progress,<br><span>every day.</span></p><div class="ft-stores"><div class="ft-download"><img class="ft-qr" src="/marketing/assets/app-download-placeholder.svg" width="140" height="140" loading="lazy" alt="iOS QR placeholder — original code to be added"><small class="ft-qr-label">Placeholder QR</small><span class="ft-store" aria-disabled="true">${brandIcon("apple")}<span><small>For iOS</small>App Store</span></span></div><div class="ft-download"><img class="ft-qr" src="/marketing/assets/app-download-placeholder.svg" width="140" height="140" loading="lazy" alt="Android QR placeholder — original code to be added"><small class="ft-qr-label">Placeholder QR</small><span class="ft-store" aria-disabled="true">${brandIcon("googleplay")}<span><small>For Android</small>Google Play</span></span></div></div></div><div class="ft-mid"><div class="ft-links">${[["Platform",[["Made for every role",href("community")],["SISU mobile app",href("mobile")],["Plans & pricing",href("plans")]]],["Get started",[["Your first steps",href("getting-started")],["Payments & billing",href("how-payments-work")],["Plan features",href("plans")],["Frequently asked questions",href("faq")]]],["Explore",[["Students","/students/"],["Teachers","/teachers/"],["Institutes","/institutes/"],["Contact us","/contact/"]]]].map(([t,ls])=>`<div><p class="ft-label">${t}</p>${ls.map(([l,u,c])=>`<a href="${u}"${c?" data-compare":""}>${l}</a>`).join("")}</div>`).join("")}</div><div class="ft-mark" aria-hidden="true"><img src="/marketing/assets/sisu-original-color.png" alt="" loading="lazy" decoding="async"></div></div>${footerSocial}<div class="ft-legal"><a class="ft-logo" href="${isHome?"#top":"/"}" aria-label="SISU Academy home"><span class="logo"><img src="/marketing/assets/sisu-original-color.png" alt="sisu."></span></a><p class="ft-note">SISU Academy brings teacher discovery, classrooms, learning resources and everyday institute work into one learning community. Class tuition is paid to the class owner; SISU plans are billed separately.</p><div class="ft-base"><p class="ft-copy">© ${new Date().getFullYear()} SISU Academy. Powered by Icorenic Pvt Ltd.</p><nav class="ft-bottom" aria-label="Footer">${out(lms("dashboard"),"Sign in to SISU","")}<a href="/contact/">Contact</a><a href="mailto:info@sisuacademylk.com">info@sisuacademylk.com</a></nav></div></div></div></footer><button type="button" class="dock" data-demo aria-label="Step inside SISU"><span>Step inside SISU<small>One 14-day trial</small></span>${arrow}</button>
<dialog class="modal" id="demo-modal" aria-labelledby="modal-title"><button type="button" class="modal-close" aria-label="Close">${icon('x')}</button>${mascot('sisu-modal')}<h2 id="modal-title">Your next chapter starts here.</h2><p>Open SISU and sign in to your own learning or teaching account.</p>${tablist('Who is stepping inside?',roles.map(r=>r.label),'role-tabs modal-tabs','md')}<ul class="ticks" id="md-panel" role="tabpanel" aria-labelledby="md-tab-0">${roles[0].items.map(i=>`<li>${i}</li>`).join('')}</ul>${out(lms('dashboard'),'Open SISU','button dark block')}<p class="fine">One 14-day trial per new account. Your account determines your access.</p></dialog>`;

document.getElementById('app').innerHTML=header+`<main id="main" class="page-${page}">${isHome?home():page==='contact'?contact():rolePage()}</main>`+footer;
document.title=isHome?'LearnVerse by SISU — Your whole learning universe.':`${page[0].toUpperCase()+page.slice(1)} — SISU Academy`;

/* ---------- behaviour ---------- */

// Fixed launch deadline: 14 days after 31 October 2026, 05:41:55 UTC.
const appLaunchAt = Date.parse('2026-11-14T05:41:55Z');
function appCountdownParts(now) {
  const seconds = Math.max(0, Math.ceil((appLaunchAt - now) / 1000));
  return [Math.floor(seconds / 86400), Math.floor(seconds / 3600) % 24, Math.floor(seconds / 60) % 60, seconds % 60];
}
const appCountdown = document.querySelector('.app-countdown');
if (appCountdown) {
  const digits = [...appCountdown.querySelectorAll('[data-countdown-unit]')];
  let countdownInterval;
  const updateCountdown = () => {
    const now = Date.now();
    const parts = appCountdownParts(now);
    digits.forEach((digit, i) => { digit.textContent = String(parts[i]).padStart(2, '0'); });
    appCountdown.setAttribute('aria-label', parts.map((part, i) => part + ' ' + ['days', 'hours', 'minutes', 'seconds'][i]).join(', ') + ' until app launch');
    if (now >= appLaunchAt) {
      appCountdown.title = 'Launch countdown complete';
      appCountdown.setAttribute('aria-label', 'Launch countdown complete');
      clearInterval(countdownInterval);
    }
  };
  countdownInterval = setInterval(updateCountdown, 1000);
  updateCountdown();
  document.addEventListener('visibilitychange', () => { if (!document.hidden) updateCountdown(); });
}

const shell=document.querySelector('.nav-shell');
const toggle=document.querySelector('.menu-toggle');
const navGroups=[...document.querySelectorAll('.nav-group')];
const closeNavGroups=()=>navGroups.forEach(group=>group.open=false);
const setMenu=open=>{if(!open)closeNavGroups();toggle.setAttribute('aria-expanded',open);toggle.setAttribute('aria-label',open?'Close menu':'Open menu');shell.classList.toggle('menu-open',open)};
toggle.addEventListener('click',()=>setMenu(toggle.getAttribute('aria-expanded')!=='true'));
document.addEventListener('click',e=>{if(shell.classList.contains('menu-open')&&!e.target.closest('.nav'))setMenu(false)});
matchMedia('(min-width:901px)').addEventListener('change',e=>{if(e.matches)setMenu(false)});
document.querySelectorAll('#navigation a').forEach(a=>a.addEventListener('click',()=>setMenu(false)));
navGroups.forEach(group=>group.querySelector('summary').addEventListener('click',()=>{navGroups.forEach(other=>{if(other!==group)other.open=false})}));
document.addEventListener('click',e=>{if(!e.target.closest('.nav-group'))closeNavGroups()});
document.addEventListener('keydown',e=>{if(e.key==='Escape'){const openGroup=navGroups.find(group=>group.open);if(openGroup)openGroup.querySelector('summary').focus();else if(shell.classList.contains('menu-open'))toggle.focus();setMenu(false)}});

const modal=document.querySelector('#demo-modal');
document.addEventListener('click',e=>{if(e.target.closest('[data-demo]')){setMenu(false);modal.showModal()}});
modal.querySelector('.modal-close').addEventListener('click',()=>modal.close());
modal.addEventListener('click',e=>{if(e.target===modal)modal.close()});

function swap(el,html){el.innerHTML=html;el.classList.remove('swap-in');void el.offsetWidth;el.classList.add('swap-in')}
function tabs(list,onSelect){if(!list)return;const btns=[...list.querySelectorAll('[role=tab]')];const panel=document.getElementById(btns[0].getAttribute('aria-controls'));const sel=(i,user)=>{btns.forEach((b,j)=>{b.setAttribute('aria-selected',j===i);b.tabIndex=j===i?0:-1});panel?.setAttribute('aria-labelledby',btns[i].id);onSelect(i,panel,user)};btns.forEach((b,i)=>{b.addEventListener('click',()=>sel(i,true));b.addEventListener('keydown',e=>{const k={ArrowRight:1,ArrowDown:1,ArrowLeft:-1,ArrowUp:-1}[e.key];if(k){e.preventDefault();const n=(i+k+btns.length)%btns.length;btns[n].focus();sel(n,true)}})});return sel}
tabs(document.querySelector('#getting-started .role-tabs'),(i,p)=>swap(p,gsPanel(starts[i])));
tabs(document.querySelector('.modal-tabs'),(i,p)=>swap(p,roles[i].items.map(t=>`<li>${t}</li>`).join('')));

// pricing: calculator total + per-card estimates follow one slider
function bindCalc(){
 const slider=document.querySelector('#seats');if(!slider)return;
 const count=document.querySelector('#seats-count'),radios=[...document.querySelectorAll('input[name="calc-plan"]')];
 const total=document.querySelector('#calc-total'),breakdown=document.querySelector('#calc-break'),notice=document.querySelector('#calc-auto');
 let n=0;
 const update=()=>{
  let i=Number(radios.find(r=>r.checked).value),shifted=false;
  while(plans[i][4]&&n>plans[i][4]&&i<plans.length-1){i++;shifted=true;}
  radios[i].checked=true;
  const [name,,base,per]=plans[i],students=n.toLocaleString('en-US'),st=students+' active student'+(n===1?'':'s');
  slider.value=n;
  slider.setAttribute('aria-valuetext',st);slider.style.setProperty('--fill',(n/slider.max*100)+'%');
  document.querySelector('#seats-max').textContent=Number(slider.max).toLocaleString('en-US');
  document.querySelector('#calc').dataset.tier=i;
  notice.textContent=shifted?'Switched to '+name+' — Individual covers up to 30 students.':'';
  total.textContent=lkr(base+per*n);
  breakdown.textContent=lkr(base)+' base + '+lkr(per)+' × '+st+', per month';
  plans.forEach(([,,b,p,c],j)=>{const el=document.querySelector('[data-est="'+j+'"]');if(!el)return;
   const over=c&&n>c;
   el.innerHTML=over?'Covers up to '+c+' students':'<strong>'+lkr(b+p*n)+'</strong><span> / month'+(n===0?' base fee':' at '+st)+'</span>';
   el.closest('.plan').classList.toggle('is-over',!!over);
  });
 };
 slider.addEventListener('input',()=>{n=Number(slider.value);count.value=n;update();});
 count.addEventListener('input',()=>{const value=Number(count.value);if(count.value===''||!Number.isFinite(value))return;count.setCustomValidity('');n=Math.min(2000,Math.max(0,Math.floor(value)));if(value!==n)count.value=n;update();});
 count.addEventListener('change',()=>{count.value=n;count.setCustomValidity('');});
 radios.forEach(r=>r.addEventListener('change',update));update();
}
bindCalc();

document.querySelector('#contact-form')?.addEventListener('submit',e=>{e.preventDefault();const f=new FormData(e.target);const text=`SISU enquiry draft\nName: ${f.get('name')}\nEmail: ${f.get('email')}\nWhatsApp: ${f.get('whatsapp') || 'Not provided'}\nRole: ${f.get('role')}\n\n${f.get('message')}\n\nDraft only — not sent.`;const u=URL.createObjectURL(new Blob([text],{type:'text/plain'}));const a=document.createElement('a');a.href=u;a.download='SISU-enquiry-draft.txt';a.click();setTimeout(()=>URL.revokeObjectURL(u),1000);document.querySelector('#form-status').textContent='Your draft has been downloaded. It has not been sent.'});

const motionMedia=window.matchMedia('(prefers-reduced-motion: reduce)');
let motionPaused=motionMedia.matches;
document.querySelectorAll('.stagger').forEach(g=>[...g.children].forEach((c,i)=>c.style.setProperty('--d',`${i*.08}s`)));
const countUp=el=>{const end=Number(el.dataset.count),t0=performance.now(),dur=900;const step=t=>{const k=Math.min(1,(t-t0)/dur);el.textContent=Math.round(end*(1-Math.pow(1-k,3)));if(k<1)requestAnimationFrame(step)};requestAnimationFrame(step);setTimeout(()=>{el.textContent=end},dur+200)};
if('IntersectionObserver' in window){const io=new IntersectionObserver(es=>es.forEach(e=>{if(e.isIntersecting){e.target.classList.add('visible');if(!motionPaused)e.target.querySelectorAll('[data-count]').forEach(countUp);io.unobserve(e.target)}}),{threshold:.12,rootMargin:'0px 0px -40px 0px'});document.querySelectorAll('.rv').forEach(el=>io.observe(el))}
else document.querySelectorAll('.rv').forEach(el=>el.classList.add('visible'));

// Feature explorer: the page's one authored moment. Auto-advances while on screen; any hover, focus or click hands control to the visitor.
const exList=document.querySelector('.ex-list');let exRestart=()=>{};
if(exList){
let featureVideo=null,featureVisible=false;
const featureObserver='IntersectionObserver' in window?new IntersectionObserver(([entry])=>{featureVisible=entry.isIntersecting;if(!featureVideo)return;if(featureVisible&&!motionPaused)featureVideo.play().catch(()=>{});else featureVideo.pause()},{threshold:.25}):null;
const watchFeatureVideo=()=>{if(featureVideo){featureObserver?.unobserve(featureVideo);featureVideo.pause()}featureVideo=document.querySelector('.workspace-recording video');featureVisible=false;if(featureVideo)featureObserver?.observe(featureVideo)};
window.featureVideoMotion=paused=>{if(!featureVideo)return;if(paused)featureVideo.pause();else if(featureVisible)featureVideo.play().catch(()=>{})};
watchFeatureVideo();
const DWELL=6500;let cur=0,timer=null,onScreen=false,hover=false,chosen=false;
// keep the active tab in view when the list is a horizontal strip (tablet and phone), without moving the page
const reveal=()=>{const b=exList.querySelector('[aria-selected=true]');if(!b||exList.scrollWidth<=exList.clientWidth)return;const x=b.getBoundingClientRect().left-exList.getBoundingClientRect().left+exList.scrollLeft-16;exList.scrollTo({left:Math.max(0,x),behavior:motionPaused?'auto':'smooth'})};
const sel=tabs(exList,(i,p,user)=>{cur=i;swap(p,exPanel(tiles[i]));watchFeatureVideo();if(user)chosen=true;reveal();exRestart()});
exRestart=()=>{clearTimeout(timer);exList.classList.remove('run');void exList.offsetWidth;if(!motionPaused&&onScreen&&!hover&&!chosen){exList.classList.add('run');timer=setTimeout(()=>sel((cur+1)%tiles.length),DWELL)}};
// a resting mouse pauses it; a tap, click or keyboard choice hands control to the visitor (touch fires pointerleave right after a tap, so only mouse pointers count as hovering)
const box=exList.closest('.explorer');box.addEventListener('pointerenter',e=>{if(e.pointerType==='mouse'){hover=true;exRestart()}});box.addEventListener('pointerleave',e=>{if(e.pointerType==='mouse'){hover=false;exRestart()}});box.addEventListener('focusin',()=>{chosen=true;exRestart()});
if('IntersectionObserver' in window)new IntersectionObserver(([e])=>{onScreen=e.isIntersecting;exRestart()},{threshold:.35}).observe(box)}

const dock=document.querySelector('.dock');
const heroVideo=document.querySelector('.hero-video'),heroContent=document.querySelector('.hero .hero-content');
// Hero depth: the scene drifts against the pointer and the copy drifts with it; scroll adds a slow parallax. One eased rAF loop drives both.
let heroY=0,hx=0,hy=0,tx=0,ty=0,heroRaf=0;
const paintHero=()=>{heroRaf=0;hx+=(tx-hx)*.07;hy+=(ty-hy)*.07;
if(heroVideo)heroVideo.style.transform=`translate3d(${(-hx*18).toFixed(2)}px,${(heroY*.14-hy*12).toFixed(2)}px,0) scale(1.08)`;
if(heroContent)heroContent.style.transform=`translate3d(${(hx*7).toFixed(2)}px,${(hy*5).toFixed(2)}px,0)`;
if(Math.abs(tx-hx)+Math.abs(ty-hy)>.002)heroRaf=requestAnimationFrame(paintHero)};
const heroEl=document.querySelector('.hero');
if(heroEl&&heroVideo&&matchMedia('(hover:hover) and (pointer:fine)').matches){
heroEl.addEventListener('pointermove',e=>{if(motionPaused)return;tx=e.clientX/innerWidth*2-1;ty=e.clientY/innerHeight*2-1;if(!heroRaf)heroRaf=requestAnimationFrame(paintHero)});
heroEl.addEventListener('pointerleave',()=>{tx=ty=0;if(!heroRaf)heroRaf=requestAnimationFrame(paintHero)})}
let ticking=false,lastY=scrollY;const narrow=matchMedia('(max-width:900px)');
function onScroll(){const y=scrollY,dy=y-lastY;shell.classList.toggle('scrolled',y>40);shell.classList.toggle('on-hero',isHome&&y<innerHeight-80);const nearEnd=y+innerHeight>document.body.scrollHeight-900;if(Math.abs(dy)>6){dock.classList.toggle('away',narrow.matches&&dy>0);lastY=y}dock.classList.toggle('show',y>innerHeight*.9&&!nearEnd);if(heroVideo&&!motionPaused&&y<innerHeight*1.2){heroY=y;if(!heroRaf)heroRaf=requestAnimationFrame(paintHero)}ticking=false}
addEventListener('scroll',()=>{if(!ticking){ticking=true;requestAnimationFrame(onScroll)}},{passive:true});onScroll();

function setMotion(paused){motionPaused=paused;document.body.classList.toggle('motion-paused',paused);document.querySelectorAll('video[autoplay],.lazy-vid[data-on]').forEach(v=>{v.muted=true;if(paused)v.pause();else v.play().catch(()=>{})});window.vpMotion?.(paused);window.featureVideoMotion?.(paused);const b=document.querySelector('.motion-control');if(b){b.innerHTML=`${icon(paused?'play':'pause')}<span>${paused?'Play motion':'Pause motion'}</span>`;b.setAttribute('aria-label',paused?'Play animations':'Pause animations')}exRestart()}
document.querySelector('.motion-control')?.addEventListener('click',()=>setMotion(!motionPaused));
// Clips only download and play while on screen (they are 3-8 MB each).
if('IntersectionObserver' in window){const vio=new IntersectionObserver(es=>es.forEach(({target:v,isIntersecting:on})=>{if(on){v.dataset.on='';if(!motionPaused)v.play().catch(()=>{})}else{delete v.dataset.on;v.pause()}}),{threshold:.25});document.querySelectorAll('.lazy-vid').forEach(v=>vio.observe(v))}
// Animated Sisu: swap each still mascot for the transparent VP9 loop once it can play.
// shortcut: Safari/iOS can't show VP9 alpha, so they keep the PNG; add an HEVC-alpha .mov if Sisu should move there too.
if(!/iPhone|iPad|Macintosh.*Version\/[\d.]+.*Safari/.test(navigator.userAgent)&&document.createElement('video').canPlayType('video/webm; codecs="vp9"'))addEventListener('load',()=>document.querySelectorAll('img.mascot').forEach(img=>{const v=document.createElement('video');Object.assign(v,{muted:true,loop:true,playsInline:true,autoplay:!motionPaused,className:img.className,src:'/marketing/assets/sisu-mascot.webm'});v.setAttribute('autoplay','');v.setAttribute('aria-hidden','true');v.width=v.height=500;v.addEventListener('loadeddata',()=>{img.replaceWith(v);if(motionPaused)v.pause()},{once:true});v.load()}));
const ftMark=document.querySelector('.ft-mark img');
if(ftMark&&matchMedia('(hover:hover)').matches){const ft=document.querySelector('.site-footer'),c=v=>Math.max(-1,Math.min(1,v));
ft.addEventListener('pointermove',e=>{if(motionPaused)return;const r=ftMark.getBoundingClientRect();ftMark.style.setProperty('--tx',`${(c((e.clientX-r.left-r.width/2)/r.width)*16).toFixed(1)}deg`);ftMark.style.setProperty('--ty',`${(c(-(e.clientY-r.top-r.height/2)/r.height)*16).toFixed(1)}deg`)},{passive:true});
ft.addEventListener('pointerleave',()=>{ftMark.style.setProperty('--tx','0deg');ftMark.style.setProperty('--ty','0deg')})}
// Orbs: the two clusters drift against each other with the scroll and lean toward the cursor.
const orbit=document.querySelector('.orbit');
if(orbit){const groups=[...orbit.querySelectorAll('.orbs')];let mx=0,my=0,queued=false;
const place=()=>{queued=false;if(motionPaused)return;const r=orbit.getBoundingClientRect();if(r.bottom<0||r.top>innerHeight)return;const p=Math.max(-1,Math.min(1,(r.top+r.height/2-innerHeight/2)/innerHeight));groups.forEach(g=>{const d=g.classList.contains('tl')?1:-1;g.style.setProperty('--sy',`${(p*-45*d).toFixed(1)}px`);g.style.setProperty('--mx',`${(mx*18*d).toFixed(1)}px`);g.style.setProperty('--my',`${(my*18*d).toFixed(1)}px`)})};
const ask=()=>{if(!queued){queued=true;requestAnimationFrame(place)}};
addEventListener('scroll',ask,{passive:true});
if(matchMedia('(hover:hover)').matches)orbit.addEventListener('pointermove',e=>{mx=e.clientX/innerWidth-.5;my=e.clientY/innerHeight-.5;ask()},{passive:true});
place()}
// Swipe rows (role cards, and plans on phones): dots follow the scroll position and jump on tap.
document.querySelectorAll('.snap').forEach(row=>{const items=[...row.children],dots=document.createElement('div');dots.className='snap-dots';
dots.innerHTML=items.map((_,i)=>`<button type="button" aria-label="Show ${i+1} of ${items.length}"></button>`).join('');row.after(dots);const btns=[...dots.children];
const at=i=>items[i].offsetLeft-items[0].offsetLeft;
const sync=()=>{const on=row.scrollWidth>row.clientWidth+4;dots.classList.toggle('on',on);if(!on)return;const x=row.scrollLeft,end=row.scrollWidth-row.clientWidth-4;let k=0,best=Infinity;items.forEach((_,i)=>{const d=Math.abs(at(i)-x);if(d<best){best=d;k=i}});if(x>=end)k=items.length-1;btns.forEach((b,i)=>b.setAttribute('aria-current',String(i===k)))};
btns.forEach((b,i)=>b.addEventListener('click',()=>row.scrollTo({left:at(i),behavior:motionPaused?'auto':'smooth'})));
row.addEventListener('scroll',sync,{passive:true});addEventListener('resize',sync,{passive:true});sync()});
// Data saver or a 2G link: keep the hero's poster instead of streaming its 6.7 MB loop.
const conn=navigator.connection;
if(heroVideo&&conn&&(conn.saveData||/2g$/.test(conn.effectiveType||''))){heroVideo.removeAttribute('autoplay');heroVideo.pause();heroVideo.querySelectorAll('source').forEach(s=>s.remove());heroVideo.load()}

// Intro video: muted autoplay while on screen (unless motion is paused), KAST-style controls, keyboard-operable.
const vp=document.querySelector('.vplayer');
if(vp){const v=vp.querySelector('video'),tog=vp.querySelector('.vp-toggle'),seek=vp.querySelector('.vp-seek'),time=vp.querySelector('.vp-time'),un=vp.querySelector('.vp-unmute'),mute=vp.querySelector('.vp-mute'),full=vp.querySelector('.vp-full');
const fmt=s=>`${Math.floor(s/60)}:${String(Math.floor(s%60)).padStart(2,'0')}`;
const paint=()=>{const playing=!v.paused;vp.dataset.state=playing?'playing':'paused';tog.innerHTML=playing?pauseIcon:playIcon;tog.setAttribute('aria-label',playing?'Pause video':'Play video')};
const setSound=on=>{v.muted=!on;if(un)un.textContent=on?'Mute':'Unmute';if(mute)mute.setAttribute('aria-label',on?'Mute video':'Unmute video');vp.classList.toggle('has-sound',on)};
let userPaused=false,visible=false;
const play=()=>{if(v.preload==='none'){v.preload='auto'}v.play().catch(()=>{});};
tog.addEventListener('click',()=>{if(v.paused){userPaused=false;play()}else{userPaused=true;v.pause()}});
v.addEventListener('click',()=>tog.click());
un?.addEventListener('click',()=>{setSound(v.muted);if(v.paused){userPaused=false;play()}});
mute?.addEventListener('click',()=>setSound(v.muted));
full.addEventListener('click',()=>{const el=vp;if(document.fullscreenElement)document.exitFullscreen();else if(el.requestFullscreen)el.requestFullscreen();else if(v.webkitEnterFullscreen)v.webkitEnterFullscreen()});
v.addEventListener('timeupdate',()=>{if(!v.duration)return;seek.value=Math.round(v.currentTime/v.duration*1000);seek.style.setProperty('--fill',`${v.currentTime/v.duration*100}%`);time.textContent=fmt(v.currentTime)});
seek.addEventListener('input',()=>{if(v.duration){v.currentTime=seek.value/1000*v.duration}});
['play','pause'].forEach(e=>v.addEventListener(e,paint));
vp.addEventListener('keydown',e=>{if((e.key===' '||e.key==='k')&&e.target===vp){e.preventDefault();tog.click()}});
if('IntersectionObserver' in window)new IntersectionObserver(([e])=>{visible=e.isIntersecting;if(visible&&!userPaused&&!motionPaused)play();else if(!visible)v.pause()},{threshold:.4}).observe(vp);
window.vpMotion=paused=>{if(paused)v.pause();else if(visible&&!userPaused)play()};paint()}
// Closing video fades up out of whatever colour the page's last section ends on.
const closingEl=document.querySelector('.closing'),lastSec=document.querySelector('#main')?.lastElementChild;
if(closingEl&&lastSec){const bg=getComputedStyle(lastSec).backgroundColor;closingEl.style.setProperty('--blend',bg==='rgba(0, 0, 0, 0)'?getComputedStyle(document.body).backgroundColor:bg)}
setMotion(motionPaused);
motionMedia.addEventListener('change',e=>setMotion(e.matches));

document.querySelectorAll('.plan-full-features summary').forEach(summary=>summary.addEventListener('click',event=>{event.preventDefault();const open=!summary.parentElement.open;document.querySelectorAll('.plan-full-features').forEach(detail=>{detail.open=open;});}));

// Continuous, gentle testimonial movement; duplicates are hidden from assistive technology.
const voiceCarousel=document.querySelector('.voice-carousel');
if(voiceCarousel){
 const track=voiceCarousel.querySelector('.voice-track'),cards=[...track.children];
 cards.forEach(card=>{const clone=card.cloneNode(true);clone.setAttribute('aria-hidden','true');clone.inert=true;clone.dataset.clone='true';track.append(clone);});
 let position=0,previous=0,visible=false,dragging=false;
 const loopWidth=()=>track.children[cards.length].offsetLeft-cards[0].offsetLeft;
 const sync=()=>{position=track.scrollLeft;};
 track.addEventListener('pointerdown',()=>{dragging=true;});
 window.addEventListener('pointerup',()=>{dragging=false;sync();});
 window.addEventListener('pointercancel',()=>{dragging=false;sync();});
 track.addEventListener('scroll',()=>{if(dragging||motionMedia.matches)sync();},{passive:true});
 track.addEventListener('wheel',()=>requestAnimationFrame(sync),{passive:true});
 track.addEventListener('keydown',event=>{if(event.key==='ArrowRight'||event.key==='ArrowLeft'){event.preventDefault();const width=loopWidth();position=(position+(event.key==='ArrowRight'?1:-1)*(cards[0].offsetWidth+24)+width)%width;track.scrollLeft=position;}});
 new IntersectionObserver(([entry])=>{visible=entry.isIntersecting;},{threshold:0}).observe(voiceCarousel);
 new ResizeObserver(()=>{position=track.scrollLeft%Math.max(loopWidth(),1);track.scrollLeft=position;}).observe(track);
 const animate=now=>{
  const elapsed=previous?Math.min(now-previous,50):0;previous=now;
  if(visible&&!document.hidden&&!motionMedia.matches&&!dragging){const width=loopWidth();if(width>0){position=(position+elapsed*.022)%width;track.scrollLeft=position;}}
  requestAnimationFrame(animate);
 };
 requestAnimationFrame(animate);
}
