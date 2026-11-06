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

/** The provenance of what a tool brings to the answer: code is Exploratory, the web is Context. */
export const TOOL_PROVENANCE: Record<StepTool, Provenance> = {
  certified: 'certified',
  code: 'exploratory',
  market: 'market',
  documents: 'documents',
  web: 'context',
};

/** The provenance labels of an answer, from the tools that ran without failing, in order. */
export function answerProvenance(steps: Array<{ tool: StepTool; status: StepStatus }>): Provenance[] {
  return [...new Set(steps.filter((step) => step.status !== 'failed').map((step) => TOOL_PROVENANCE[step.tool]))];
}

export const STATUSES: Record<StepStatus, string> = {
  running: 'Running',
  done: 'Done',
  failed: 'Failed',
};
