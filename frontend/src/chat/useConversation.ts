import { useCallback, useEffect, useReducer, useRef } from 'react';
import { useApi } from '../api/ApiContext';
import { ApiError } from '../api/client';
import { conversationReducer, EMPTY } from './conversation';

const CUT_OFF = 'The answer was cut off before the end. Ask again.';

/** The conversation about one dataset: its turns, and `ask` to send a message. */
export function useConversation(datasetId: string) {
  const api = useApi();
  const [state, dispatch] = useReducer(conversationReducer, EMPTY);
  const controller = useRef<AbortController | null>(null);
  const count = useRef(0);

  useEffect(() => () => controller.current?.abort(), []);

  const ask = useCallback(
    async (message: string) => {
      const text = message.trim();
      if (!text || controller.current) return;
      count.current += 1;
      dispatch({ type: 'asked', id: `q${count.current}`, text });

      const abort = new AbortController();
      controller.current = abort;
      let ended = false;
      try {
        const request = { dataset_id: datasetId, conversation_id: state.conversationId, message: text };
        for await (const event of api.chat(request, abort.signal)) {
          dispatch({ type: 'event', event });
          if (event.type === 'done' || event.type === 'error') ended = true;
        }
        if (!ended && !abort.signal.aborted) dispatch({ type: 'failed', message: CUT_OFF });
      } catch (error) {
        if (!abort.signal.aborted) {
          dispatch({ type: 'failed', message: error instanceof ApiError ? error.message : CUT_OFF });
        }
      } finally {
        controller.current = null;
      }
    },
    // The input is disabled while an answer streams: the next message always sees the latest id.
    [api, datasetId, state.conversationId],
  );

  return { ...state, ask };
}
