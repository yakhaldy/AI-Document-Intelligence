export const DOC_TYPE_LABELS = {
  invoice: 'Facture',
  contract: 'Contrat',
  report: 'Rapport',
}

export function docTypeLabel(docType) {
  return DOC_TYPE_LABELS[docType] ?? docType ?? '—'
}
