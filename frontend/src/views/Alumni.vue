<script setup>
import { onMounted, ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import { Plus, Search, Pencil, Trash2, ChevronLeft, ChevronRight, FileSpreadsheet } from 'lucide-vue-next';
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

const statusOptions = [
  { value: '', label: 'Semua Status' },
  { value: 'BELUM_DILACAK', label: 'Belum Dilacak' },
  { value: 'TERVERIFIKASI_MANUAL', label: 'Terverifikasi (Manual)' },
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
  searchTimeout = setTimeout(() => load(1), 350);
});
watch(statusFilter, () => load(1));

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
  load(page);
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
              <th class="pb-3 font-medium">Nama Lulusan</th>
              <th class="pb-3 font-medium">Fakultas / Program Studi</th>
              <th class="pb-3 font-medium">Tanggal Lulus</th>
              <th class="pb-3 font-medium">Status</th>
              <th class="pb-3 font-medium text-right">Aksi</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="alumni in alumniStore.items" :key="alumni.id" class="border-b border-border last:border-0">
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
  </div>
</template>
