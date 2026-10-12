import type { Draft } from '../../api/drafts';

/** The sources of the draft: each claim with the passage of the policy that supports it. */
export function Citations({ draft }: { draft: Draft }) {
  const policy = draft.policy_answer;
  if (!policy) return <p className="muted">This draft has no sources. Check every fact in it yourself.</p>;
  if (!policy.answerable || draft.citations.length === 0) {
    return (
      <p className="notice">
        The policy documents do not answer “{policy.question}”. Do not promise anything about it without checking.
      </p>
    );
  }
  return (
    <section className="citations" aria-label="Sources">
      <h4>Sources (policy question: {policy.question})</h4>
      <ol>
        {draft.citations.map((c, i) => (
          <li key={`${c.id}-${i}`}>
            <p>{c.claim}</p>
            <blockquote cite={`#passage-${c.id}`}>
              {c.quote}
              <footer>
                {c.document}, section “{c.section}” ({c.version})
              </footer>
            </blockquote>
          </li>
        ))}
      </ol>
    </section>
  );
}
