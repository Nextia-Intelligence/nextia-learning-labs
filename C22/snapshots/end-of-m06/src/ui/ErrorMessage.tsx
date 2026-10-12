import { describeError } from '../lib/errors';

/** An error in words, with a button to try again only when trying again can help. */
export function ErrorMessage({ error, onRetry }: { error: Error; onRetry?: () => void }) {
  const { text, canRetry } = describeError(error);
  return (
    <div className="error" role="alert">
      <p>{text}</p>
      {onRetry && canRetry && (
        <button type="button" onClick={onRetry}>
          Try again
        </button>
      )}
    </div>
  );
}
