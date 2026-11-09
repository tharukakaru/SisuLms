"""Idempotent transform of the deployed marketing app; retain all unrelated content."""
import re
MARKER='/* SISU shared plan catalogue v1 */'
def patch_marketing(source):
    if MARKER in source:return source
    def replace(pattern,replacement):
        nonlocal source
        source,n=re.subn(pattern,lambda m:replacement,source,count=1,flags=re.S)
        if n!=1:raise RuntimeError('Marketing template changed; no website files modified')
    replace(r'const plans=\[.*?;\s*const activeNote=', '''const catalogEscape=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let sharedCatalog=null;
try{
 const response=await fetch('/api/method/institute_lms.plan_catalog.public_catalog',{cache:'no-store',credentials:'omit',signal:AbortSignal.timeout(5000)});
 if(!response.ok)throw Error('Catalogue unavailable');
 const body=await response.json();
 if(!body.message?.plans)throw Error('Catalogue unavailable');
 sharedCatalog=body.message;
}catch(e){sharedCatalog=null;}
const plans=sharedCatalog?['Individual','Silver','Gold','Platinum'].map((name,i)=>{
 const p=sharedCatalog.plans[name];
 return [name,catalogEscape(p.description),p.monthly_lkr,p.active_student_lkr,i===0?30:0,p.card_features];
}):[];
const activeNote=''')
    replace(r'const compareRows=\[.*?;\s*const pricingGroups=\[.*?;', '''const comparisonLabels={news:'News publishing',integrations:'Connected teaching tools',expenses:'Expense register',custom_domain:'Custom domain',view_limits:'Video view controls',reviews:'Class reviews',watermark:'Video watermark',tute_delivery:'Tute delivery',white_label:'Institute branding'};
const compareRows=[['Base monthly fee',...plans.map(p=>lkr(p[2]))],['Per active student / month',...plans.map(p=>lkr(p[3]))],...Object.entries(comparisonLabels).map(([key,label])=>[label,...plans.map(p=>sharedCatalog.plans[p[0]].features[key]?1:0)])];
const pricingGroups=[['Included tools',compareRows.map((_,i)=>i)]];''')
    replace(r'const planFeatureValue=\(row,i\)=>\{.*?\};', 'const planFeatureValue=(row,i)=>compareRows[row][i+1];')
    replace(r'const cardFeatureList=i=>\{.*?\};\s*const cell=', '''const cardFeatureList=i=>'<ul class="plan-feature-list plan-highlights">'+plans[i][5].map(text=>'<li class="feature-included"><span class="feature-state" aria-hidden="true">&#10003;</span><span class="feature-copy">'+catalogEscape(text)+'</span></li>').join('')+'</ul>';
const cell=''')
    source=source.replace("const pricingBlock=(title,sub,plansFirst=false)=>{", "const pricingBlock=(title,sub,plansFirst=false)=>{\nif(!sharedCatalog)return '<section class=\"section\" id=\"plans\"><div class=\"wrap\"><h2>Subscription plans</h2><p>Plans are temporarily unavailable. Please refresh to try again.</p></div></section>';" )
    source=source.replace('LKR 2,500</span>', '${plans.length?lkr(plans[0][2]):\'Loading...\'}</span>')
    replace(r"\['How do package charges work\?','.*?'\]", "['How do package charges work?','Each plan has a monthly base fee plus active-student usage. See the current plan cards and calculator for published prices. Class tuition is separate.']")
    return MARKER+'\n(async()=>{\n'+source+'\n})();\n'
