import test from 'node:test';
import assert from 'node:assert/strict';
import { createAppearanceMotion } from '../src/appearance-motion.ts';

function harness({reduced=false, supported=true, throwing=false}={}) {
  const callbacks = [];
  const transitions = [];
  const applied = [];
  const settled = [];
  const animated = [];
  let currentReduced = reduced;
  const motion = createAppearanceMotion({
    reducedMotion:()=>currentReduced,
    setAnimating:active=>animated.push(active),
    apply:theme=>{applied.push(theme);return theme !== 'light';},
    onApplied:(theme,saved)=>settled.push({theme,saved}),
    startTransition: supported ? update=>{
      if(throwing) throw new Error('Unavailable');
      let rejectReady, finish;
      const transition = { ready:new Promise((_resolve,reject)=>{rejectReady=reject;}), finished:new Promise(resolve=>{finish=resolve;}), skipped:false, skipTransition(){this.skipped=true;rejectReady(new Error('Skipped'));}, finish:()=>finish() };
      callbacks.push(update); transitions.push(transition); return transition;
    } : undefined,
  });
  return {motion, callbacks, transitions, applied, settled, animated, setReduced:value=>{currentReduced=value;}};
}
test('unsupported View Transitions apply immediately and keep the storage result',()=>{
  const h=harness({supported:false}); h.motion.change('light');
  assert.deepEqual(h.applied,['light']);
  assert.deepEqual(h.settled,[{theme:'light',saved:false}]);
  assert.deepEqual(h.animated,[false]);
});
test('reduced motion bypasses native snapshots and applies the theme immediately',()=>{
  const h=harness({reduced:true}); h.motion.change('dark');
  assert.equal(h.callbacks.length,0); assert.deepEqual(h.applied,['dark']);
});
test('rapid requests skip obsolete transitions and reject their out-of-order updates',async()=>{
  const h=harness();
  h.motion.change('light'); h.motion.change('dark'); h.motion.change('light');
  h.callbacks[2](); h.callbacks[0](); h.callbacks[1]();
  assert.deepEqual(h.applied,['light']);
  assert.deepEqual(h.settled,[{theme:'light',saved:false}]);
  assert.ok(h.transitions[0].skipped && h.transitions[1].skipped);
  h.transitions[0].finish(); h.transitions[1].finish();
  await new Promise(resolve=>setImmediate(resolve));
  assert.equal(h.animated.at(-1),true);
  h.transitions[2].finish();
  await new Promise(resolve=>setImmediate(resolve));
  assert.equal(h.animated.at(-1),false);
});
test('turning reduced motion on during a sequence invalidates the older callback',()=>{
  const h=harness(); h.motion.change('light'); h.setReduced(true); h.motion.change('dark');
  h.callbacks[0](); assert.deepEqual(h.applied,['dark']); assert.equal(h.animated.at(-1),false);
});
test('a browser transition startup failure falls back without losing the requested theme',()=>{
  const h=harness({throwing:true});h.motion.change('light');
  assert.deepEqual(h.applied,['light']);assert.equal(h.animated.at(-1),false);
});
test('disposing cancels the visual transition and ignores pending callbacks',()=>{
  const h=harness();h.motion.change('light');h.motion.dispose();h.callbacks[0]();
  assert.ok(h.transitions[0].skipped);assert.deepEqual(h.applied,[]);assert.equal(h.animated.at(-1),false);
});
