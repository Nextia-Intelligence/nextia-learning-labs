// Helpers for the labs' own timings: the time until the browser has painted the change.

/** Resolves after the next paint: one frame to draw, one more to be sure it is on the screen. */
export function afterNextPaint(): Promise<number> {
  return new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(() => resolve(performance.now()))));
}

export const ms = (n: number) => `${n.toFixed(1)} ms`;
