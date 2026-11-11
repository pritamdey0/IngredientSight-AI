/**
 * Soft light leak in the corner of a panel. Purely decorative, no dependencies.
 */

import React from 'react';

export interface SpotlightProps {
  className?: string;
  size?: number;
}

export const Spotlight: React.FC<SpotlightProps> = ({ className = '', size = 260 }) => (
  <div
    aria-hidden="true"
    className={`pointer-events-none absolute -left-20 -top-24 select-none ${className}`}
    style={{
      width: size,
      height: size,
      background:
        'radial-gradient(circle at center, rgba(255,255,255,0.18) 0%, rgba(255,255,255,0.06) 45%, transparent 72%)',
    }}
  />
);

export default Spotlight;
