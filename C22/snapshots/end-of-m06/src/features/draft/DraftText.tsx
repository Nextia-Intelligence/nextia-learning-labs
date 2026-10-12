import { renderMarkdown } from './markdown';

/** A finished draft, with its Markdown shown as formatted text. Only cleaned HTML reaches the page. */
export default function DraftText({ text }: { text: string }) {
  return <div className="draft-text markdown" dangerouslySetInnerHTML={{ __html: renderMarkdown(text) }} />;
}
