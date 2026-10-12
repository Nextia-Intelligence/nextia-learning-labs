/**
 * A short message for screen readers, read when it changes ("polite": after what the user hears
 * now). It is for changes of state only; never put every streamed piece of text here.
 */
export function LiveRegion({ message }: { message: string }) {
  return (
    <p className="visually-hidden" role="status" aria-live="polite" aria-atomic="true">
      {message}
    </p>
  );
}
