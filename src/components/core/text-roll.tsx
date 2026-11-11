/**
 * Dependency-free TextRoll: each character rises into place on mount.
 *
 * The animation lives in `.roll-char` in `src/index.css` so it also honours
 * `prefers-reduced-motion`. The element that owns the text must carry the real
 * label (`aria-label`), because these spans are decorative.
 */

import React from 'react';

export interface TextRollProps {
  children: string;
  className?: string;
  delayMs?: number;
  staggerMs?: number;
}

export const TextRoll: React.FC<TextRollProps> = ({
  children,
  className = '',
  delayMs = 0,
  staggerMs = 26,
}) => {
  let cursor = 0;

  return (
    <span className={`inline-block ${className}`} aria-hidden="true">
      {children.split(' ').map((word, wordIndex, words) => {
        const characters = Array.from(word).map((character, index) => (
          <span
            key={`${character}-${index}`}
            className="roll-char"
            style={{ animationDelay: `${delayMs + (cursor + index) * staggerMs}ms` }}
          >
            {character}
          </span>
        ));
        cursor += word.length;

        return (
          <React.Fragment key={`${word}-${wordIndex}`}>
            <span className="inline-block whitespace-nowrap">{characters}</span>
            {wordIndex < words.length - 1 ? ' ' : null}
          </React.Fragment>
        );
      })}
    </span>
  );
};

export default TextRoll;
