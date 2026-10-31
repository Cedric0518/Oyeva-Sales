import { render, screen, within } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { UPLOAD_EXAMPLE } from '../../api/mock/uploadExample';
import type { Dataset } from '../../api/types';
import { DataReport } from './DataReport';

function renderReport(changes: Partial<Dataset> = {}) {
  const dataset: Dataset = { ...structuredClone(UPLOAD_EXAMPLE), ...changes };
  render(<DataReport dataset={dataset} />);
}

function section(name: string) {
  return screen.getByRole('region', { name });
}

describe('DataReport', () => {
  it('sums up the file', () => {
    renderReport();
    expect(screen.getByText('atlas_sales.xlsx')).toBeInTheDocument();
    expect(screen.getByText('59,764 rows · 2 sheets (Orders, Targets) · Ontario')).toBeInTheDocument();
  });

  it('writes each check status in words, with its amount', () => {
    renderReport();
    const checks = section('Checks');
    expect(within(checks).getByText('6 warnings, 2 OK')).toBeInTheDocument();

    const duplicates = within(checks).getByText('Duplicate rows').closest('li')!;
    expect(within(duplicates).getByText('Warning')).toBeInTheDocument();
    expect(within(duplicates).getByText('12 duplicate rows', { exact: false })).toBeInTheDocument();
    expect(within(duplicates).getByText('$176.83')).toBeInTheDocument();

    const returns = within(checks).getByText('Returns').closest('li')!;
    expect(within(returns).getByText('OK')).toBeInTheDocument();
    expect(within(returns).getByText('-$13,190.44')).toBeInTheDocument();
  });

  it('lists the recognized column of each role', () => {
    renderReport();
    const roles = section('Column roles');
    expect(within(roles).getByText('Unit price').nextElementSibling).toHaveTextContent('unit_price');
    expect(within(roles).getByText('Target').nextElementSibling).toHaveTextContent('Targets.target');
    expect(within(roles).queryByRole('alert')).not.toBeInTheDocument();
  });

  it('says when certified metrics cannot run', () => {
    renderReport({ roles: { ...UPLOAD_EXAMPLE.roles, amount: null, target: null } });
    const roles = section('Column roles');
    expect(within(roles).getByText('No amount column recognized')).toBeInTheDocument();
    expect(within(roles).getByText(/refuse to run/)).toBeInTheDocument();
    expect(within(roles).getAllByText('Not found')).toHaveLength(2);
  });

  it('describes a converted document', () => {
    renderReport();
    const card = section('Your document');
    expect(within(card).getByText('atlas_context.pdf')).toBeInTheDocument();
    expect(within(card).getByText('PDF')).toBeInTheDocument();
    expect(within(card).getByText('Converted from PDF')).toBeInTheDocument();
    expect(within(card).getByText('Whole document')).toBeInTheDocument();
    expect(within(card).getByText('Sections').nextElementSibling).toHaveTextContent('10');
    expect(within(card).getByText('Set aside').nextElementSibling).toHaveTextContent('None');
  });

  it('names the search mode and Word conversion', () => {
    renderReport({ context: { ...UPLOAD_EXAMPLE.context!, name: 'manual.docx', format: 'docx', mode: 'rag' } });
    const card = section('Your document');
    expect(within(card).getByText('Converted from Word')).toBeInTheDocument();
    expect(within(card).getByText('Search')).toBeInTheDocument();
  });

  it('lists the sections set aside and why', () => {
    renderReport({
      context: {
        ...UPLOAD_EXAMPLE.context!,
        removed_sections: [{ id: 'D4', title: 'Column dictionary', reason: 'Flagged by Prompt Shields' }],
      },
    });
    const card = section('Your document');
    expect(within(card).getByText('1 section set aside at upload')).toBeInTheDocument();
    expect(within(card).getByText('Column dictionary', { selector: 'strong' })).toBeInTheDocument();
    expect(within(card).getByText(/Flagged by Prompt Shields/)).toBeInTheDocument();
  });

  it('says when there is no document', () => {
    renderReport({ context: null });
    expect(within(section('Your document')).getByText('No document added')).toBeInTheDocument();
  });
});
