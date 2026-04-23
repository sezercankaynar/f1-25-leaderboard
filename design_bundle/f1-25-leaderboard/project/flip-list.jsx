// FlipList — animates child reordering using the FLIP technique.
// Children are rendered in the order `items` is given; when items re-order,
// every row slides to its new Y smoothly.

function FlipList({ items, keyFn, children }) {
  const containerRef = React.useRef(null);
  const positionsRef = React.useRef(new Map()); // key -> top (px) before paint

  // measure BEFORE paint (layout effect) so we capture positions from the
  // previous render, then compute deltas after the new layout.
  React.useLayoutEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    const children = Array.from(container.children);
    const prev = positionsRef.current;
    const next = new Map();

    children.forEach((child) => {
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

window.FlipList = FlipList;
