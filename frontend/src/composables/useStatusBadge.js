const STATUS_MAP = {
  BELUM_DILACAK: { label: 'Belum Dilacak', variant: 'outline' },
  TERVERIFIKASI_MANUAL: { label: 'Terverifikasi (Manual)', variant: 'success' },
};

export function useStatusBadge() {
  const statusInfo = (status) => STATUS_MAP[status] || { label: status, variant: 'outline' };
  return { statusInfo };
}
