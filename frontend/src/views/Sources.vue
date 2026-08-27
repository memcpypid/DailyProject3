<script setup>
import { onMounted, ref } from 'vue';
import { Plus, Pencil, Trash2 } from 'lucide-vue-next';
import { useSourceStore } from '@/stores/sources';
import Card from '@/components/ui/Card.vue';
import Button from '@/components/ui/Button.vue';
import Badge from '@/components/ui/Badge.vue';
import Skeleton from '@/components/ui/Skeleton.vue';
import SourceModal from '@/components/modals/SourceModal.vue';
import ConfirmModal from '@/components/modals/ConfirmModal.vue';

const sourceStore = useSourceStore();

const modalOpen = ref(false);
const editingSource = ref(null);
const confirmOpen = ref(false);
const deletingSource = ref(null);
const deleting = ref(false);

onMounted(() => sourceStore.fetchList());

const openCreate = () => {
  editingSource.value = null;
  modalOpen.value = true;
};
const openEdit = (source) => {
  editingSource.value = source;
  modalOpen.value = true;
};

const toggleEnabled = (source) => {
  sourceStore.update(source.id, { enabled: !source.enabled });
};

const askDelete = (source) => {
  deletingSource.value = source;
  confirmOpen.value = true;
};
const confirmDelete = async () => {
  deleting.value = true;
  try {
    await sourceStore.remove(deletingSource.value.id);
    confirmOpen.value = false;
  } finally {
    deleting.value = false;
  }
};
</script>

<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h1 class="text-3xl font-bold tracking-tight text-foreground">Sumber Data</h1>
        <p class="text-muted-foreground mt-2">
          Kelola daftar sumber publik yang bisa dipilih periset saat mencatat temuan manual, beserta catatan
          bobot kepercayaan masing-masing sebagai referensi (tidak dipakai otomatis oleh sistem).
        </p>
      </div>
      <Button @click="openCreate">
        <template #icon-left><Plus class="w-4 h-4 mr-2" /></template>
        Tambah Sumber
      </Button>
    </div>

    <Card body-class="p-4 sm:p-6">
      <div v-if="sourceStore.loading" class="space-y-3">
        <Skeleton v-for="i in 6" :key="i" height="3rem" />
      </div>

      <div v-else class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="text-left text-muted-foreground border-b border-border">
              <th class="pb-3 font-medium">Nama Sumber</th>
              <th class="pb-3 font-medium">Cara Akses</th>
              <th class="pb-3 font-medium">Bobot</th>
              <th class="pb-3 font-medium">Status</th>
              <th class="pb-3 font-medium text-right">Aksi</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="source in sourceStore.items" :key="source.id" class="border-b border-border last:border-0">
              <td class="py-3 font-medium text-foreground">{{ source.name }}</td>
              <td class="py-3 text-muted-foreground">{{ source.access_type || '-' }}</td>
              <td class="py-3">
                <div class="flex items-center gap-2 w-32">
                  <div class="h-1.5 flex-1 bg-secondary rounded-full overflow-hidden">
                    <div class="h-full bg-primary rounded-full" :style="{ width: `${source.weight * 100}%` }"></div>
                  </div>
                  <span class="text-xs text-muted-foreground w-8">{{ source.weight.toFixed(2) }}</span>
                </div>
              </td>
              <td class="py-3">
                <button @click="toggleEnabled(source)">
                  <Badge :variant="source.enabled ? 'success' : 'outline'" custom-class="cursor-pointer">
                    {{ source.enabled ? 'Aktif' : 'Nonaktif' }}
                  </Badge>
                </button>
              </td>
              <td class="py-3">
                <div class="flex justify-end gap-1">
                  <Button size="icon" variant="ghost" title="Edit" @click="openEdit(source)">
                    <Pencil class="w-4 h-4" />
                  </Button>
                  <Button size="icon" variant="ghost" title="Hapus" @click="askDelete(source)">
                    <Trash2 class="w-4 h-4 text-rose-500" />
                  </Button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </Card>

    <SourceModal :is-open="modalOpen" :source="editingSource" @close="modalOpen = false" @success="sourceStore.fetchList()" />

    <ConfirmModal :is-open="confirmOpen" title="Hapus Sumber Data"
      :message="`Yakin ingin menghapus sumber ${deletingSource?.name}?`"
      confirm-text="Hapus" type="danger" :is-loading="deleting" @close="confirmOpen = false" @confirm="confirmDelete" />
  </div>
</template>
