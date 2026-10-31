import { useRef, useState, type DragEvent } from 'react';
import { CircleAlert, Upload, X, type LucideIcon } from 'lucide-react';
import { cx } from '../../cx';
import { formatBytes } from '../../format';
import styles from './DropZone.module.css';

interface DropZoneProps {
  id: string;
  label: string;
  hint: string;
  accept: string;
  optional?: boolean;
  icon: LucideIcon;
  file: File | null;
  error: string | null;
  disabled?: boolean;
  onSelect: (file: File) => void;
  onClear: () => void;
}

/** A file field: drop a file on the zone, or choose one with the button. */
export function DropZone({
  id,
  label,
  hint,
  accept,
  optional = false,
  icon: Icon,
  file,
  error,
  disabled = false,
  onSelect,
  onClear,
}: DropZoneProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const hintId = `${id}-hint`;
  const errorId = `${id}-error`;

  function onDragOver(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    if (!disabled) setDragging(true);
  }

  function onDragLeave(event: DragEvent<HTMLDivElement>) {
    if (!event.currentTarget.contains(event.relatedTarget as Node | null)) setDragging(false);
  }

  function onDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setDragging(false);
    const dropped = event.dataTransfer.files[0];
    if (dropped && !disabled) onSelect(dropped);
  }

  return (
    <div className={styles.field}>
      <div className={styles.labelRow}>
        <label htmlFor={id} className={styles.label}>
          {label}
        </label>
        <span className={styles.tag}>{optional ? 'Optional' : 'Required'}</span>
      </div>
      <p id={hintId} className={styles.hint}>
        {hint}
      </p>

      {file ? (
        <div className={styles.selected}>
          <Icon size={20} aria-hidden="true" className={styles.fileIcon} />
          <div className={styles.fileText}>
            <span className={styles.fileName}>{file.name}</span>
            <span className={cx(styles.fileSize, 'tabular')}>{formatBytes(file.size)}</span>
          </div>
          <button
            type="button"
            className={styles.remove}
            onClick={onClear}
            disabled={disabled}
            aria-label={`Remove ${file.name}`}
          >
            <X size={16} aria-hidden="true" />
          </button>
        </div>
      ) : (
        <div
          className={cx(styles.zone, dragging && styles.dragging, error && styles.invalid, disabled && styles.disabled)}
          onDragOver={onDragOver}
          onDragLeave={onDragLeave}
          onDrop={onDrop}
        >
          <Upload size={20} aria-hidden="true" className={styles.zoneIcon} />
          <p>
            Drop the file here, or{' '}
            <button
              type="button"
              className={styles.browse}
              onClick={() => inputRef.current?.click()}
              disabled={disabled}
              aria-describedby={error ? `${hintId} ${errorId}` : hintId}
            >
              choose a file
            </button>
          </p>
        </div>
      )}

      <input
        ref={inputRef}
        id={id}
        type="file"
        accept={accept}
        className="visually-hidden"
        tabIndex={-1}
        disabled={disabled}
        aria-describedby={hintId}
        onChange={(event) => {
          const chosen = event.target.files?.[0];
          // Reset so that choosing the same file again still fires a change.
          event.target.value = '';
          if (chosen) onSelect(chosen);
        }}
      />

      {error && (
        <p id={errorId} role="alert" className={styles.error}>
          <CircleAlert size={16} aria-hidden="true" />
          {error}
        </p>
      )}
    </div>
  );
}
