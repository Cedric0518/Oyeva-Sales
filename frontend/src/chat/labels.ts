import type { Provenance, StepStatus, StepTool } from '../api/types';

/** The five provenance labels (frontend/CLAUDE.md, section 4). The name is always written out. */
export const PROVENANCE: Record<Provenance, { label: string; tooltip: string }> = {
  certified: { label: 'Certified', tooltip: 'Computed by a tested function with a fixed definition.' },
  exploratory: {
    label: 'Exploratory',
    tooltip: 'Computed by code the assistant wrote for this question. Review the code.',
  },
  market: { label: 'Market', tooltip: 'Official statistics (Statistics Canada), fetched by code.' },
  documents: { label: 'Your documents', tooltip: 'From the document you uploaded. Not a calculation.' },
  context: { label: 'Context', tooltip: 'From the web. Not computed from your data.' },
};

export const TOOLS: Record<StepTool, string> = {
  certified: 'Certified metric',
  code: 'Code Interpreter',
  market: 'Market data',
  documents: 'Your documents',
  web: 'Web search',
};

export const STATUSES: Record<StepStatus, string> = {
  running: 'Running',
  done: 'Done',
  failed: 'Failed',
};
