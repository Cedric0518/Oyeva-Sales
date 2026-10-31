import type { ReactNode } from 'react';
import { FileSpreadsheet, RotateCcw } from 'lucide-react';
import logoUrl from '../../assets/oyeva-logo.svg';
import { Button } from '../ui/Button';
import styles from './AppShell.module.css';

interface AppShellProps {
  /** Name of the loaded sales file, or null on the upload screen. */
  datasetName: string | null;
  /** Shown in the header when the app runs on the mock backend. */
  mockBackend?: boolean;
  /** A new session is a page reload (docs/contract.md, section 1). */
  onNewSession?: () => void;
  children: ReactNode;
}

function reloadPage() {
  window.location.reload();
}

export function AppShell({ datasetName, mockBackend = false, onNewSession = reloadPage, children }: AppShellProps) {
  return (
    <div className={styles.shell}>
      <header className={styles.header}>
        <img src={logoUrl} alt="Oyeva Sales" className={styles.logo} width={143} height={28} />
        {datasetName && (
          <>
            <span className={styles.divider} aria-hidden="true" />
            <p className={styles.dataset}>
              <FileSpreadsheet size={16} aria-hidden="true" />
              <span className="visually-hidden">Dataset: </span>
              <span className={styles.datasetName} title={datasetName}>
                {datasetName}
              </span>
            </p>
          </>
        )}
        <span className={styles.spacer} />
        {mockBackend && <span className={styles.mode}>Mock backend</span>}
        <Button variant="ghost" onClick={onNewSession}>
          <RotateCcw size={16} aria-hidden="true" />
          New session
        </Button>
      </header>
      <main className={styles.main}>{children}</main>
    </div>
  );
}
