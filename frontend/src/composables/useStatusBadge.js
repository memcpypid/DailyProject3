const STATUS_MAP = {
  BELUM_DILACAK: { label: 'Belum Dilacak', variant: 'outline' },
  TERVERIFIKASI_OTOMATIS: { label: 'Terverifikasi Otomatis', variant: 'success' },
  TERVERIFIKASI_MANUAL: { label: 'Terverifikasi (Manual)', variant: 'success' },
  PERLU_TINJAUAN_MANUAL: { label: 'Perlu Tinjauan Manual', variant: 'warning' },
  TIDAK_DITEMUKAN: { label: 'Tidak Ditemukan', variant: 'danger' },
};

export function useStatusBadge() {
  const statusInfo = (status) => STATUS_MAP[status] || { label: status, variant: 'outline' };
  return { statusInfo };
}
