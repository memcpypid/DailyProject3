<script setup>
import { onMounted, ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import { Plus, Search, Pencil, Trash2, ChevronLeft, ChevronRight, FileSpreadsheet, ListChecks, ExternalLink, X } from 'lucide-vue-next';
import { useAlumniStore } from '@/stores/alumni';
import { useStatusBadge } from '@/composables/useStatusBadge';
import Card from '@/components/ui/Card.vue';
import Button from '@/components/ui/Button.vue';
import Input from '@/components/ui/Input.vue';
import Select from '@/components/ui/Select.vue';
import Badge from '@/components/ui/Badge.vue';
import Skeleton from '@/components/ui/Skeleton.vue';
import AlumniModal from '@/components/modals/AlumniModal.vue';
import ImportAlumniModal from '@/components/modals/ImportAlumniModal.vue';
import ConfirmModal from '@/components/modals/ConfirmModal.vue';

const alumniStore = useAlumniStore();
const router = useRouter();
const { statusInfo } = useStatusBadge();

const search = ref('');
const statusFilter = ref('');

const modalOpen = ref(false);
const importModalOpen = ref(false);
const editingAlumni = ref(null);
const confirmOpen = ref(false);
const deletingAlumni = ref(null);
const deleting = ref(false);
const selectedIds = ref([]);
const batchPanelOpen = ref(false);

const statusOptions = [
  { value: '', label: 'Semua Status' },
  { value: 'BELUM_DILACAK', label: 'Belum Dilacak' },
  { value: 'TERVERIFIKASI_OTOMATIS', label: 'Terverifikasi Otomatis' },
  { value: 'TERVERIFIKASI_MANUAL', label: 'Terverifikasi (Manual)' },
  { value: 'PERLU_TINJAUAN_MANUAL', label: 'Perlu Tinjauan Manual' },
  { value: 'TIDAK_DITEMUKAN', label: 'Tidak Ditemukan' },
];

const load = (page = 1) => {
  alumniStore.fetchList({
    page,
    limit: alumniStore.pagination.limit,
    search: search.value || undefined,
    status: statusFilter.value || undefined,
  });
};

onMounted(() => load(1));

let searchTimeout;
watch(search, () => {
  clearTimeout(searchTimeout);
  selectedIds.value = [];
  searchTimeout = setTimeout(() => load(1), 350);
});
watch(statusFilter, () => {
  selectedIds.value = [];
  load(1);
});

const openCreate = () => {
  editingAlumni.value = null;
  modalOpen.value = true;
};
const openEdit = (alumni) => {
  editingAlumni.value = alumni;
  modalOpen.value = true;
};
const onModalSuccess = () => load(alumniStore.pagination.page);

const askDelete = (alumni) => {
  deletingAlumni.value = alumni;
  confirmOpen.value = true;
};
const confirmDelete = async () => {
  deleting.value = true;
  try {
    await alumniStore.remove(deletingAlumni.value.id);
    confirmOpen.value = false;
    load(alumniStore.pagination.page);
  } finally {
    deleting.value = false;
  }
};

const goToPage = (page) => {
  if (page < 1 || page > alumniStore.pagination.total_pages) return;
  selectedIds.value = [];
  load(page);
};

const allVisibleSelected = () =>
  alumniStore.items.length > 0 && alumniStore.items.every((item) => selectedIds.value.includes(item.id));

const toggleAllVisible = () => {
  const visibleIds = alumniStore.items.map((item) => item.id);
  if (allVisibleSelected()) {
    selectedIds.value = selectedIds.value.filter((id) => !visibleIds.includes(id));
  } else {
    selectedIds.value = [...new Set([...selectedIds.value, ...visibleIds])];
  }
};

const selectedAlumni = () => alumniStore.items.filter((item) => selectedIds.value.includes(item.id));

const searchTargetsFor = (alumni) => {
  const identity = [alumni.full_name, alumni.nim, alumni.program_studi, alumni.fakultas]
    .filter(Boolean)
    .map((value) => `"${value}"`)
    .join(' ');
  const targets = [
    ['Media sosial', `${identity} LinkedIn OR Instagram OR Facebook OR TikTok`],
    ['Email dan nomor HP', `${identity} email OR telepon OR WhatsApp`],
    ['Tempat dan alamat bekerja', `${identity} bekerja OR perusahaan OR instansi`],
    ['Posisi dan jenis pekerjaan', `${identity} jabatan OR posisi OR PNS OR swasta OR wirausaha`],
    ['Media sosial tempat bekerja', `${identity} perusahaan LinkedIn OR Instagram OR Facebook`],
  ];
  return targets.map(([label, query]) => ({
    label,
    url: `https://www.google.com/search?q=${encodeURIComponent(query)}`,
  }));
};
</script>

<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h1 class="text-3xl font-bold tracking-tight text-foreground">Data Alumni</h1>
        <p class="text-muted-foreground mt-2">Kelola profil alumni dan catat temuan hasil riset manual.</p>
      </div>
      <div class="flex gap-2">
        <Button variant="outline" :disabled="!selectedIds.length" @click="batchPanelOpen = true">
          <template #icon-left><ListChecks class="w-4 h-4 mr-2" /></template>
          Pencarian Batch ({{ selectedIds.length }})
        </Button>
        <Button variant="outline" @click="importModalOpen = true">
          <template #icon-left><FileSpreadsheet class="w-4 h-4 mr-2" /></template>
          Impor Excel
        </Button>
        <Button @click="openCreate">
          <template #icon-left><Plus class="w-4 h-4 mr-2" /></template>
          Tambah Alumni
        </Button>
      </div>
    </div>

    <div class="flex items-start gap-3 rounded-lg border border-primary/20 bg-primary/5 px-4 py-3 text-sm text-foreground">
      <Search class="mt-0.5 h-4 w-4 shrink-0 text-primary" />
      <p>Silakan tekan <strong>Nama Lulusan</strong> untuk dapat mencari data.</p>
    </div>

    <Card body-class="p-4 sm:p-6">
      <div class="flex flex-col sm:flex-row gap-4 mb-6">
        <Input id="search" v-model="search" placeholder="Cari nama atau NIM..." custom-class="flex-1">
          <template #icon-left><Search class="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" /></template>
        </Input>
        <Select id="status-filter" v-model="statusFilter" :options="statusOptions" custom-class="sm:w-64" />
      </div>

      <div v-if="alumniStore.loading" class="space-y-3">
        <Skeleton v-for="i in 5" :key="i" height="3rem" />
      </div>

      <div v-else-if="!alumniStore.items.length" class="text-center py-12 text-muted-foreground">
        Belum ada data alumni. Klik "Tambah Alumni" untuk memulai.
      </div>

      <div v-else class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="text-left text-muted-foreground border-b border-border">
              <th class="pb-3 pr-3 font-medium">
                <input type="checkbox" :checked="allVisibleSelected()" aria-label="Pilih semua alumni pada halaman ini"
                  class="h-4 w-4 rounded border-border" @change="toggleAllVisible" />
              </th>
              <th class="pb-3 font-medium">Nama Lulusan</th>
              <th class="pb-3 font-medium">Fakultas / Program Studi</th>
              <th class="pb-3 font-medium">Tanggal Lulus</th>
              <th class="pb-3 font-medium">Status</th>
              <th class="pb-3 font-medium text-right">Aksi</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="alumni in alumniStore.items" :key="alumni.id" class="border-b border-border last:border-0">
              <td class="py-3 pr-3">
                <input v-model="selectedIds" type="checkbox" :value="alumni.id"
                  :aria-label="`Pilih ${alumni.full_name}`" class="h-4 w-4 rounded border-border" />
              </td>
              <td class="py-3">
                <router-link :to="`/app/alumni/${alumni.id}`" class="font-medium text-foreground hover:text-primary hover:underline">
                  {{ alumni.full_name }}
                </router-link>
                <p class="text-xs text-muted-foreground">{{ alumni.nim }}</p>
              </td>
              <td class="py-3 text-foreground">
                {{ alumni.fakultas || '-' }}
                <span v-if="alumni.program_studi" class="text-muted-foreground"> &middot; {{ alumni.program_studi }}</span>
              </td>
              <td class="py-3 text-foreground">{{ alumni.tanggal_lulus || '-' }}</td>
              <td class="py-3">
                <Badge :variant="statusInfo(alumni.status).variant">{{ statusInfo(alumni.status).label }}</Badge>
              </td>
              <td class="py-3">
                <div class="flex justify-end gap-1">
                  <Button size="icon" variant="ghost" title="Edit" @click="openEdit(alumni)">
                    <Pencil class="w-4 h-4" />
                  </Button>
                  <Button size="icon" variant="ghost" title="Hapus" @click="askDelete(alumni)">
                    <Trash2 class="w-4 h-4 text-rose-500" />
                  </Button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="alumniStore.pagination.total_pages > 1" class="flex items-center justify-between mt-6 pt-4 border-t border-border">
        <p class="text-sm text-muted-foreground">
          Halaman {{ alumniStore.pagination.page }} dari {{ alumniStore.pagination.total_pages }}
          ({{ alumniStore.pagination.total }} alumni)
        </p>
        <div class="flex gap-2">
          <Button size="sm" variant="outline" :disabled="!alumniStore.pagination.has_previous"
            @click="goToPage(alumniStore.pagination.page - 1)">
            <ChevronLeft class="w-4 h-4" />
          </Button>
          <Button size="sm" variant="outline" :disabled="!alumniStore.pagination.has_next"
            @click="goToPage(alumniStore.pagination.page + 1)">
            <ChevronRight class="w-4 h-4" />
          </Button>
        </div>
      </div>
    </Card>

    <AlumniModal :is-open="modalOpen" :alumni="editingAlumni" @close="modalOpen = false" @success="onModalSuccess" />

    <ImportAlumniModal :is-open="importModalOpen" @close="importModalOpen = false" @success="onModalSuccess" />

    <ConfirmModal :is-open="confirmOpen" title="Hapus Alumni"
      :message="`Yakin ingin menghapus data ${deletingAlumni?.full_name}? Tindakan ini tidak dapat dibatalkan.`"
      confirm-text="Hapus" type="danger" :is-loading="deleting" @close="confirmOpen = false" @confirm="confirmDelete" />

    <div v-if="batchPanelOpen" class="fixed inset-0 z-50 overflow-y-auto" role="dialog" aria-modal="true">
      <div class="fixed inset-0 bg-black/10 backdrop-blur-sm" @click="batchPanelOpen = false"></div>
      <div class="flex min-h-screen items-end justify-center p-4 sm:items-center">
        <div class="relative w-full max-w-3xl rounded-lg border border-border bg-card shadow-xl" @click.stop>
          <div class="flex items-start justify-between border-b border-border p-5">
            <div>
              <h3 class="text-lg font-semibold text-foreground">Pencarian Batch Tanpa API</h3>
              <p class="mt-1 text-xs text-muted-foreground">
                Buka tautan satu per satu, verifikasi hasilnya, lalu simpan melalui Input Manual. Sistem tidak melakukan scraping atau penyimpanan otomatis.
              </p>
            </div>
            <button class="text-muted-foreground hover:text-foreground" @click="batchPanelOpen = false"><X class="h-5 w-5" /></button>
          </div>
          <div class="max-h-[70vh] space-y-4 overflow-y-auto p-5">
            <div v-for="alumni in selectedAlumni()" :key="alumni.id" class="rounded-lg border border-border p-4">
              <p class="font-semibold text-foreground">{{ alumni.full_name }}</p>
              <p class="text-xs text-muted-foreground">NIM {{ alumni.nim || '-' }} · {{ alumni.program_studi || '-' }}</p>
              <div class="mt-3 flex flex-wrap gap-2">
                <a v-for="target in searchTargetsFor(alumni)" :key="target.label" :href="target.url" target="_blank" rel="noopener noreferrer"
                  class="inline-flex items-center gap-1.5 rounded-md border border-input bg-background px-3 py-2 text-xs font-medium text-foreground hover:bg-accent">
                  {{ target.label }} <ExternalLink class="h-3.5 w-3.5" />
                </a>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
