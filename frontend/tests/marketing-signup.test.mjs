import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
test('marketing signup stays on the LMS host and opens signup directly',()=>{
 const app=readFileSync(new URL('../../marketing-site/app.js',import.meta.url),'utf8');
 const portal=readFileSync(new URL('../src/native/PortalRoot.vue',import.meta.url),'utf8');
 assert.ok(app.includes("const base='';"));
 assert.ok(app.includes('/campus?signup=1'));
 assert.ok(!app.includes('https://staging.sisuacademylk.com'));
 assert.ok(portal.includes("signup=ref(new URLSearchParams(location.search).get('signup')==='1')"));
});
test('marketing resource namespace preserves Frappe assets',()=>{
 const html=readFileSync(new URL('../../marketing-site/index.html',import.meta.url),'utf8');
 assert.ok(html.includes('/marketing/app.js'));
 assert.ok(html.includes('/marketing/style.css'));
 assert.ok(!html.includes('href="/assets/'));
});
