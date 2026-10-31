import { useReducer } from 'react';
import { ApiContext } from './api/ApiContext';
import type { ApiClient } from './api/client';
import type { Dataset } from './api/types';
import { AppShell } from './components/AppShell/AppShell';
import { UploadPanel } from './components/UploadPanel/UploadPanel';
import { Workspace } from './components/Workspace/Workspace';

type State = { screen: 'upload' } | { screen: 'workspace'; dataset: Dataset };

type Action = { type: 'dataset_loaded'; dataset: Dataset };

function reducer(_state: State, action: Action): State {
  switch (action.type) {
    case 'dataset_loaded':
      return { screen: 'workspace', dataset: action.dataset };
  }
}

interface AppProps {
  client: ApiClient;
  mockBackend?: boolean;
  onNewSession?: () => void;
}

export function App({ client, mockBackend = false, onNewSession }: AppProps) {
  const [state, dispatch] = useReducer(reducer, { screen: 'upload' });

  return (
    <ApiContext value={client}>
      <AppShell
        datasetName={state.screen === 'workspace' ? state.dataset.file_name : null}
        mockBackend={mockBackend}
        onNewSession={onNewSession}
      >
        {state.screen === 'upload' ? (
          <UploadPanel onLoaded={(dataset) => dispatch({ type: 'dataset_loaded', dataset })} />
        ) : (
          <Workspace dataset={state.dataset} />
        )}
      </AppShell>
    </ApiContext>
  );
}
