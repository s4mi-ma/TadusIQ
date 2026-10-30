import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { runInNewContext } from 'node:vm';
import { applyAppearance } from '../src/appearance.ts';
const bootstrap = readFileSync(new URL('../public/appearance.js', import.meta.url), 'utf8');
const documentStub = () => ({documentElement:{dataset:{},style:{}},querySelector:()=>({setAttribute(){}})});
test('bootstrap defaults dark and restores only valid light preference before rendering', () => {
  for (const [saved, expected] of [[null,'dark'],['light','light'],['dark','dark'],['unexpected','dark']]) {
    const document = documentStub();
    runInNewContext(bootstrap, {document,localStorage:{getItem:()=>saved}});
    assert.equal(document.documentElement.dataset.theme, expected);
    assert.equal(document.documentElement.style.colorScheme, expected);
  }
});
test('blocked storage does not prevent boot or changing theme for the current visit', () => {
  const document = documentStub();
  runInNewContext(bootstrap, {document,get localStorage(){throw new Error('blocked');}});
  assert.equal(document.documentElement.dataset.theme,'dark');
  const originalDoc = globalThis.document;
  const originalStorage = Object.getOwnPropertyDescriptor(globalThis,'localStorage');
  globalThis.document = document;
  Object.defineProperty(globalThis,'localStorage',{configurable:true,get(){throw new Error('blocked');}});
  try {
    assert.equal(applyAppearance('light'),false);
    assert.equal(document.documentElement.dataset.theme,'light');
  } finally {
    if (originalDoc === undefined) delete globalThis.document; else globalThis.document = originalDoc;
    if (originalStorage) Object.defineProperty(globalThis,'localStorage',originalStorage); else delete globalThis.localStorage;
  }
});
test('only the appearance preference is persisted', () => {
  const originalDoc = globalThis.document;
  const originalStorage = Object.getOwnPropertyDescriptor(globalThis,'localStorage');
  globalThis.document = documentStub();
  const saved = [];
  Object.defineProperty(globalThis,'localStorage',{configurable:true,value:{setItem:(...args)=>saved.push(args)}});
  try {
    assert.equal(applyAppearance('light'),true);
    assert.deepEqual(saved,[['rapidready-appearance','light']]);
  } finally {
    if (originalDoc === undefined) delete globalThis.document; else globalThis.document = originalDoc;
    if (originalStorage) Object.defineProperty(globalThis,'localStorage',originalStorage); else delete globalThis.localStorage;
  }
});
const css = readFileSync(new URL('../src/styles.css',import.meta.url),'utf8');
const luminance = color => {
  const hex = color.length === 4 ? '#'+color.slice(1).split('').map(char=>char+char).join('') : color;
  return [1,3,5].map(index=>parseInt(hex.slice(index,index+2),16)/255).map(value=>value<=.04045?value/12.92:((value+.055)/1.055)**2.4).reduce((sum,value,index)=>sum+value*[.2126,.7152,.0722][index],0);
};
test('both themes meet text and primary hover contrast targets', () => {
  let tokens = {};
  for (const selector of [':root {',':root[data-theme=light] {']) {
    const block = css.slice(css.indexOf(selector)).split('}')[0];
    tokens = {...tokens,...Object.fromEntries([...block.matchAll(/(--[\w-]+):\s*(#[\da-f]+)/gi)].map(match=>[match[1],match[2]]))};
    for (const [foreground,background] of [['text','surface'],['muted','surface'],['muted','canvas'],['on-primary','primary'],['on-primary','primary-hover'],['on-primary','primary-pressed'],['success','success-bg'],['warning','warning-bg'],['danger','danger-bg'],['selected-text','selected-bg']]) {
      const values = [tokens['--'+foreground],tokens['--'+background]].map(luminance).sort((a,b)=>a-b);
      const ratio = (values[1]+.05)/(values[0]+.05);
      assert.ok(ratio>=4.5,`${selector} ${foreground}/${background}: ${ratio}`);
    }
  }
});
test('neutral focus indicators remain distinguishable from both theme surfaces', () => {
  let tokens = {};
  for (const selector of [':root {', ':root[data-theme=light] {']) {
    const block = css.slice(css.indexOf(selector)).split('}')[0];
    tokens = {...tokens,...Object.fromEntries([...block.matchAll(/(--[\w-]+):\s*(#[\da-f]+)/gi)].map(match=>[match[1],match[2]]))};
    for(const background of ['surface','canvas']) {
      const values=[tokens['--focus'],tokens['--'+background]].map(luminance).sort((a,b)=>a-b);
      assert.ok((values[1]+.05)/(values[0]+.05)>=3,`${selector} focus/${background}`);
    }
  }
});
