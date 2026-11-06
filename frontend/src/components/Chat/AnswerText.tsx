import Markdown, { type Components } from 'react-markdown';
import type { Citation, WebSource } from '../../api/types';
import { findReference, linkReferences, visibleText } from '../../chat/references';
import { CitationChip } from './CitationChip';
import styles from './Chat.module.css';

interface AnswerTextProps {
  text: string;
  streaming: boolean;
  citations: Citation[];
  sources: WebSource[];
}

/** The answer in Markdown (no raw HTML, no images), with `[D6]` and `[W1]` drawn as chips. */
export function AnswerText({ text, streaming, citations, sources }: AnswerTextProps) {
  const markdown = linkReferences(visibleText(text, streaming), citations, sources, !streaming);

  const components: Components = {
    a({ href, children }) {
      if (href?.startsWith('#ref-')) {
        const id = href.slice('#ref-'.length);
        return <CitationChip id={id} reference={findReference(id, citations, sources)} />;
      }
      return (
        <a href={href} target="_blank" rel="noopener noreferrer">
          {children}
        </a>
      );
    },
  };

  return (
    <div className={styles.prose}>
      <Markdown skipHtml disallowedElements={['img']} components={components}>
        {markdown}
      </Markdown>
    </div>
  );
}
