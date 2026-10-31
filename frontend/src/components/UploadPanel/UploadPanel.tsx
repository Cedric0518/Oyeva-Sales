import { useEffect, useState, type FormEvent } from 'react';
import { FileSpreadsheet, FileText, LoaderCircle } from 'lucide-react';
import { useApi } from '../../api/ApiContext';
import { toApiError } from '../../api/client';
import type { Dataset, ProvinceCode } from '../../api/types';
import { DEFAULT_PROVINCE, PROVINCES } from '../../provinces';
import {
  CONTEXT_FILE_ACCEPT,
  SALES_FILE_ACCEPT,
  validateContextFile,
  validateSalesFile,
} from '../../upload/validation';
import { Button } from '../ui/Button';
import { Notice } from '../ui/Notice';
import { DropZone } from './DropZone';
import styles from './UploadPanel.module.css';

interface UploadPanelProps {
  onLoaded: (dataset: Dataset) => void;
}

type Busy = null | 'upload' | 'sample';

export function UploadPanel({ onLoaded }: UploadPanelProps) {
  const api = useApi();
  const [salesFile, setSalesFile] = useState<File | null>(null);
  const [salesError, setSalesError] = useState<string | null>(null);
  const [contextFile, setContextFile] = useState<File | null>(null);
  const [contextError, setContextError] = useState<string | null>(null);
  const [region, setRegion] = useState<ProvinceCode>(DEFAULT_PROVINCE);
  const [busy, setBusy] = useState<Busy>(null);
  const [requestError, setRequestError] = useState<string | null>(null);

  // A file dropped next to a zone would make the browser open it and lose the session.
  useEffect(() => {
    const block = (event: DragEvent) => event.preventDefault();
    window.addEventListener('dragover', block);
    window.addEventListener('drop', block);
    return () => {
      window.removeEventListener('dragover', block);
      window.removeEventListener('drop', block);
    };
  }, []);

  function selectSales(file: File) {
    const problem = validateSalesFile(file);
    setSalesFile(problem ? null : file);
    setSalesError(problem?.message ?? null);
    setRequestError(null);
  }

  function selectContext(file: File) {
    const problem = validateContextFile(file);
    setContextFile(problem ? null : file);
    setContextError(problem?.message ?? null);
    setRequestError(null);
  }

  async function run(kind: Exclude<Busy, null>, call: () => Promise<Dataset>) {
    setBusy(kind);
    setRequestError(null);
    try {
      onLoaded(await call());
    } catch (error) {
      setRequestError(toApiError(error).message);
      setBusy(null);
    }
  }

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!salesFile || busy) return;
    void run('upload', () => api.upload({ file: salesFile, region, context: contextFile }));
  }

  const disabled = busy !== null;

  return (
    <div className={styles.page}>
      <div className={styles.intro}>
        <h1 className={styles.title}>Start with your sales file</h1>
        <p className={styles.lead}>
          Oyeva Sales checks your file, then answers your questions in plain English. Every number shows where it
          comes from.
        </p>
      </div>

      <form className={styles.card} onSubmit={onSubmit} aria-busy={busy === 'upload'} noValidate>
        <DropZone
          id="sales-file"
          label="Sales file"
          hint="CSV or Excel (.xlsx), up to 20 MB."
          accept={SALES_FILE_ACCEPT}
          icon={FileSpreadsheet}
          file={salesFile}
          error={salesError}
          disabled={disabled}
          onSelect={selectSales}
          onClear={() => setSalesFile(null)}
        />

        <DropZone
          id="context-file"
          label="About your business"
          optional
          hint="Markdown, PDF or Word, up to 5 MB and 50 pages. What the columns mean, store closures, promotions, returns policy: answers cite the section they use."
          accept={CONTEXT_FILE_ACCEPT}
          icon={FileText}
          file={contextFile}
          error={contextError}
          disabled={disabled}
          onSelect={selectContext}
          onClear={() => setContextFile(null)}
        />

        <div className={styles.field}>
          <label htmlFor="region" className={styles.label}>
            Province or territory
          </label>
          <p id="region-hint" className={styles.hint}>
            Your sales are compared with the retail trade of your province, excluding motor vehicle and parts dealers
            and gasoline stations (Statistics Canada).
          </p>
          <select
            id="region"
            className={styles.select}
            value={region}
            onChange={(event) => setRegion(event.target.value as ProvinceCode)}
            disabled={disabled}
            aria-describedby="region-hint"
          >
            {PROVINCES.map((p) => (
              <option key={p.code} value={p.code}>
                {p.name}
              </option>
            ))}
          </select>
        </div>

        {requestError && (
          <Notice tone="error" title="The file could not be checked" role="alert">
            <p>{requestError}</p>
          </Notice>
        )}

        <div className={styles.actions}>
          <Button type="submit" variant="primary" size="large" disabled={!salesFile || disabled}>
            {busy === 'upload' ? (
              <>
                <LoaderCircle size={18} aria-hidden="true" className={styles.spinner} />
                Checking your file...
              </>
            ) : (
              'Check my file'
            )}
          </Button>
          {!salesFile && !busy && <p className={styles.hint}>Add a sales file to continue.</p>}
        </div>
      </form>

      <section className={styles.sample} aria-labelledby="sample-title">
        <div>
          <h2 id="sample-title" className={styles.sampleTitle}>
            No file at hand?
          </h2>
          <p className={styles.hint}>
            Try Atlas General Store, a fictional Ontario retailer: two years of sales and its company notes.
          </p>
        </div>
        <Button
          variant="secondary"
          onClick={() => void run('sample', () => api.sample())}
          disabled={disabled}
          aria-busy={busy === 'sample'}
        >
          {busy === 'sample' ? (
            <>
              <LoaderCircle size={16} aria-hidden="true" className={styles.spinner} />
              Loading the sample...
            </>
          ) : (
            'Use sample data'
          )}
        </Button>
      </section>
    </div>
  );
}
