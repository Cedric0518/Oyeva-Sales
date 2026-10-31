import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import { MockApiClient } from './api/mock/MockApiClient';
import { App } from './App';
import { makeFile } from './test/files';

describe('App on the mock backend', () => {
  it('goes from the upload screen to the data report', async () => {
    const user = userEvent.setup();
    render(<App client={new MockApiClient({ delayMs: 0 })} mockBackend />);

    expect(screen.getByRole('heading', { name: 'Start with your sales file' })).toBeInTheDocument();
    expect(screen.getByText('Mock backend')).toBeInTheDocument();

    await user.upload(screen.getByLabelText('Sales file'), makeFile('atlas_sales.xlsx'));
    await user.click(screen.getByRole('button', { name: 'Check my file' }));

    expect(await screen.findByRole('complementary', { name: 'Data report' })).toBeInTheDocument();
    expect(screen.getByRole('region', { name: 'Checks' })).toBeInTheDocument();
    expect(screen.getByRole('banner')).toHaveTextContent('atlas_sales.xlsx');
    expect(screen.getByText('No document added')).toBeInTheDocument();
  });

  it('loads the sample with its document', async () => {
    const user = userEvent.setup();
    render(<App client={new MockApiClient({ delayMs: 0 })} />);

    await user.click(screen.getByRole('button', { name: 'Use sample data' }));

    expect(await screen.findByText('atlas_context.md')).toBeInTheDocument();
    expect(screen.getByText('Markdown')).toBeInTheDocument();
    expect(screen.queryByText(/Converted from/)).not.toBeInTheDocument();
  });

  it('starts a new session from the header', async () => {
    const user = userEvent.setup();
    const onNewSession = vi.fn();
    render(<App client={new MockApiClient({ delayMs: 0 })} onNewSession={onNewSession} />);

    await user.click(screen.getByRole('button', { name: 'New session' }));
    expect(onNewSession).toHaveBeenCalledOnce();
  });
});
