import type { Appearance } from './appearance';

type MotionTransition = { ready: Promise<unknown>; finished: Promise<unknown>; skipTransition: () => void };
type Options = {
  startTransition?: (update: () => void) => MotionTransition;
  reducedMotion: () => boolean;
  setAnimating: (active: boolean) => void;
  apply: (theme: Appearance) => boolean;
  onApplied: (theme: Appearance, saved: boolean) => void;
};

// Keep delayed browser snapshot callbacks from restoring an obsolete theme.
export function createAppearanceMotion(options: Options) {
  let generation = 0;
  let active: MotionTransition | undefined;
  return {
    change(theme: Appearance) {
      const request = ++generation;
      active?.skipTransition();
      active = undefined;
      const update = () => {
        if (request !== generation) return;
        const saved = options.apply(theme);
        options.onApplied(theme, saved);
      };
      if (!options.startTransition || options.reducedMotion()) {
        options.setAnimating(false);
        update();
        return;
      }
      options.setAnimating(true);
      try {
        const transition = options.startTransition(update);
        active = transition;
        // ready rejects when an obsolete transition is skipped. The DOM update still runs.
        void transition.ready.catch(() => {});
        void transition.finished.catch(() => {}).then(() => {
          if (request !== generation) return;
          active = undefined;
          options.setAnimating(false);
        });
      } catch {
        options.setAnimating(false);
        update();
      }
    },
    dispose() {
      generation++;
      active?.skipTransition();
      active = undefined;
      options.setAnimating(false);
    },
  };
}
