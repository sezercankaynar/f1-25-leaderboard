import { useLayoutEffect, useRef } from 'react';

export default function FlipList({ items, keyFn, children }) {
  const containerRef = useRef(null);
  const positionsRef = useRef(new Map());

  useLayoutEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    const rows = Array.from(container.children);
    const prev = positionsRef.current;
    const next = new Map();

    rows.forEach((child) => {
      const key = child.getAttribute('data-flip-key');
      const rect = child.getBoundingClientRect();
      next.set(key, rect.top);
      const prevTop = prev.get(key);
      if (prevTop != null && prevTop !== rect.top) {
        const dy = prevTop - rect.top;
        child.animate(
          [
            { transform: `translateY(${dy}px)` },
            { transform: 'translateY(0)' },
          ],
          { duration: 420, easing: 'cubic-bezier(.22,.9,.35,1)' }
        );
      }
    });
    positionsRef.current = next;
  });

  return (
    <div ref={containerRef}>
      {items.map((item, i) => (
        <div key={keyFn(item)} data-flip-key={keyFn(item)}>
          {children(item, i)}
        </div>
      ))}
    </div>
  );
}
