import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import { ApiContext } from '../../api/ApiContext';
import { ApiError, type ApiClient } from '../../api/client';
import { UPLOAD_EXAMPLE } from '../../api/mock/uploadExample';
import { makeFile } from '../../test/files';
import { UploadPanel } from './UploadPanel';

function fakeApi(overrides: Partial<ApiClient> = {}): ApiClient {
  return {
    health: vi.fn(async () => ({ status: 'ok' as const })),
    upload: vi.fn(async () => structuredClone(UPLOAD_EXAMPLE)),
    sample: vi.fn(async () => structuredClone(UPLOAD_EXAMPLE)),
    ...overrides,
  };
}

function renderPanel(api: ApiClient = fakeApi()) {
  const onLoaded = vi.fn();
  // applyAccept: false lets the tests pick files the input would hide, as a drop would.
  const user = userEvent.setup({ applyAccept: false });
  render(
    <ApiContext value={api}>
      <UploadPanel onLoaded={onLoaded} />
    </ApiContext>,
  );
  return { api, onLoaded, user };
}

const submitButton = () => screen.getByRole('button', { name: 'Check my file' });

describe('UploadPanel', () => {
  it('waits for a sales file before it can be sent', async () => {
    const { user } = renderPanel();
    expect(submitButton()).toBeDisabled();

    await user.upload(screen.getByLabelText('Sales file'), makeFile('atlas_sales.xlsx'));

    expect(screen.getByText('atlas_sales.xlsx')).toBeInTheDocument();
    expect(submitButton()).toBeEnabled();
  });

  it('refuses a file of the wrong format, with the reason', async () => {
    const { user } = renderPanel();
    await user.upload(screen.getByLabelText('Sales file'), makeFile('report.pdf'));

    expect(screen.getByRole('alert')).toHaveTextContent('"report.pdf" is not a sales file we can read.');
    expect(submitButton()).toBeDisabled();
  });

  it('refuses a document over 5 MB', async () => {
    const { user } = renderPanel();
    await user.upload(screen.getByLabelText('About your business'), makeFile('notes.pdf', 6 * 1024 * 1024));
    expect(screen.getByRole('alert')).toHaveTextContent('The limit is 5 MB.');
  });

  it('defaults to Ontario', () => {
    renderPanel();
    expect(screen.getByLabelText('Province or territory')).toHaveValue('ON');
  });

  it('sends the file, the province and the document', async () => {
    const { api, onLoaded, user } = renderPanel();
    const sales = makeFile('atlas_sales.xlsx');
    const notes = makeFile('atlas_context.pdf');

    await user.upload(screen.getByLabelText('Sales file'), sales);
    await user.upload(screen.getByLabelText('About your business'), notes);
    await user.selectOptions(screen.getByLabelText('Province or territory'), 'Quebec');
    await user.click(submitButton());

    expect(api.upload).toHaveBeenCalledWith({ file: sales, region: 'QC', context: notes });
    await waitFor(() => expect(onLoaded).toHaveBeenCalledOnce());
  });

  it('can remove a chosen file', async () => {
    const { user } = renderPanel();
    await user.upload(screen.getByLabelText('Sales file'), makeFile('atlas_sales.xlsx'));
    await user.click(screen.getByRole('button', { name: 'Remove atlas_sales.xlsx' }));
    expect(screen.queryByText('atlas_sales.xlsx')).not.toBeInTheDocument();
    expect(submitButton()).toBeDisabled();
  });

  it('shows the server message when the upload fails', async () => {
    const message = 'We could not read "empty.csv": the file is empty.';
    const api = fakeApi({ upload: vi.fn(async () => Promise.reject(new ApiError('unreadable_file', message, 422))) });
    const { onLoaded, user } = renderPanel(api);

    await user.upload(screen.getByLabelText('Sales file'), makeFile('empty.csv'));
    await user.click(submitButton());

    expect(await screen.findByRole('alert')).toHaveTextContent(message);
    expect(onLoaded).not.toHaveBeenCalled();
    expect(submitButton()).toBeEnabled();
  });

  it('loads the sample data', async () => {
    const { api, onLoaded, user } = renderPanel();
    await user.click(screen.getByRole('button', { name: 'Use sample data' }));
    expect(api.sample).toHaveBeenCalledOnce();
    await waitFor(() => expect(onLoaded).toHaveBeenCalledOnce());
  });
});
