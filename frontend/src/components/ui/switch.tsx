// Adapted from shadcn/ui's MIT-licensed new-york-v4 Switch.
// https://github.com/shadcn-ui/ui/blob/main/apps/v4/registry/new-york-v4/ui/switch.tsx
// CSS classes and the individual Radix import replace Tailwind/cn and the umbrella package.
// Full attribution: frontend/THIRD_PARTY_NOTICES.md.
import type { ComponentProps } from 'react';
import * as SwitchPrimitive from '@radix-ui/react-switch';

export function Switch({ className = '', ...props }: ComponentProps<typeof SwitchPrimitive.Root>) {
  return <SwitchPrimitive.Root data-slot="switch" className={`ui-switch ${className}`} {...props}>
    <SwitchPrimitive.Thumb data-slot="switch-thumb" className="ui-switch-thumb" />
  </SwitchPrimitive.Root>;
}
