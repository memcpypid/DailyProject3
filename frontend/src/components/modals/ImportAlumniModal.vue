<script setup>
import { ref, watch } from 'vue';
import { X, CloudUpload, FileSpreadsheet, CheckCircle2, AlertTriangle } from 'lucide-vue-next';
import { useAlumniStore } from '@/stores/alumni';
import Button from '@/components/ui/Button.vue';

const props = defineProps({
  isOpen: { type: Boolean, required: true },
});

const emit = defineEmits(['close', 'success']);
const alumniStore = useAlumniStore();

const fileInput = ref(null);
const selectedFile = ref(null);
const preview = ref(null);
const errorMsg = ref('');
const previewing = ref(false);

watch(
  () => props.isOpen,
  (open) => {
    if (!open) return;
    selectedFile.value = null;
    preview.value = null;
    errorMsg.value = '';
  }
);

const onFileChange = (e) => {
  selectedFile.value = e.target.files?.[0] || null;
  preview.value = null;
  errorMsg.value = '';
};

const runPreview = async () => {
  if (!selectedFile.value) return;
  errorMsg.value = '';
  previewing.value = true;
  try {
    preview.value = await alumniStore.importExcel(selectedFile.value, { dryRun: true });
  } catch (err) {
    errorMsg.value = err.response?.data?.detail || err.message || 'Gagal membaca file';
  } finally {
    previewing.value = false;
  }
};

const confirmImport = async () => {
  if (!selectedFile.value) return;
  errorMsg.value = '';
  try {
    await alumniStore.importExcel(selectedFile.value, { dryRun: false });
    emit('success');
    emit('close');
  } catch (err) {
    errorMsg.value = err.response?.data?.detail || err.message || 'Impor gagal';
  }
};
</script>

<template>
  <div v-if="isOpen" class="fixed inset-0 z-50 overflow-y-auto" role="dialog" aria-modal="true">
    <div class="fixed inset-0 bg-black/10 backdrop-blur-sm" @click="!alumniStore.importing && emit('close')"></div>

    <div class="flex min-h-screen items-end justify-center p-4 text-center sm:items-center sm:p-0">
      <div class="relative overflow-hidden rounded-lg bg-card text-left shadow-xl sm:my-8 sm:w-full sm:max-w-lg border border-border" @click.stop>
        <div class="px-4 pb-4 pt-5 sm:p-6">
          <div class="flex justify-between items-center mb-2">
            <h3 class="text-lg font-semibold text-foreground">Impor Data Alumni (Excel)</h3>
            <button @click="emit('close')" :disabled="alumniStore.importing" class="text-muted-foreground hover:text-foreground">
              <X class="w-5 h-5" />
            </button>
          </div>
          <p class="text-xs text-muted-foreground mb-5">
            Kolom wajib persis: <b>Nama Lulusan, NIM, Tahun Masuk, Tanggal Lulus, Fakultas, Program Studi</b>.
            Baris dengan NIM yang sudah ada di akun ini otomatis dilewati.
          </p>

          <div v-if="errorMsg" class="mb-4 p-3 text-sm bg-rose-500/10 text-rose-500 border border-rose-500/20 rounded-lg">
            {{ errorMsg }}
          </div>

          <input ref="fileInput" type="file" accept=".xlsx,.xls,.csv" class="hidden" @change="onFileChange" />

          <button
            class="w-full flex flex-col items-center justify-center gap-2 border-2 border-dashed border-border rounded-lg py-8 text-muted-foreground hover:border-primary hover:text-primary transition-colors"
            @click="fileInput.click()">
            <FileSpreadsheet v-if="selectedFile" class="w-8 h-8" />
            <CloudUpload v-else class="w-8 h-8" />
            <span class="text-sm">{{ selectedFile ? selectedFile.name : 'Klik untuk pilih file .xlsx / .xls / .csv' }}</span>
          </button>

          <div v-if="preview" class="mt-4 p-4 rounded-lg border border-border bg-secondary/40 text-sm space-y-1">
            <p class="flex items-center gap-2 text-foreground font-medium">
              <CheckCircle2 class="w-4 h-4 text-emerald-500" /> Pratinjau: {{ preview.total_rows }} baris terbaca
            </p>
            <p class="text-muted-foreground">{{ preview.created }} baru akan ditambahkan</p>
            <div v-if="preview.skipped_duplicate" class="text-muted-foreground">
              <p>{{ preview.skipped_duplicate }} dilewati (NIM sudah ada), rinciannya:</p>
              <ul class="list-disc list-inside pl-2">
                <li v-if="preview.skipped_duplicate_in_file">
                  {{ preview.skipped_duplicate_in_file }} NIM duplikat di dalam file itu sendiri (baris lain di
                  file yang sama sudah pakai NIM tersebut lebih dulu)
                </li>
                <li v-if="preview.skipped_duplicate_in_db">
                  {{ preview.skipped_duplicate_in_db }} NIM sudah tersimpan di database akun ini sebelumnya
                </li>
              </ul>
            </div>
            <p v-if="preview.skipped_invalid" class="text-amber-500 flex items-center gap-1.5">
              <AlertTriangle class="w-3.5 h-3.5" /> {{ preview.skipped_invalid }} baris tidak valid (Nama/NIM kosong)
            </p>
            <div v-if="preview.errors?.length" class="mt-1">
              <p class="text-xs text-muted-foreground font-medium">Contoh baris yang dilewati:</p>
              <ul class="text-xs text-muted-foreground list-disc list-inside">
                <li v-for="(err, i) in preview.errors" :key="i">{{ err }}</li>
              </ul>
            </div>
          </div>

          <div class="pt-5 flex justify-end gap-3 border-t border-border mt-6">
            <Button type="button" variant="outline" @click="emit('close')" :disabled="alumniStore.importing" customClass="w-full sm:w-auto">
              Batal
            </Button>
            <Button v-if="!preview" key="preview-btn" type="button" :disabled="!selectedFile" :loading="previewing"
              @click="runPreview" customClass="w-full sm:w-auto">
              Pratinjau
            </Button>
            <Button v-else key="confirm-btn" type="button" :loading="alumniStore.importing" @click="confirmImport" customClass="w-full sm:w-auto">
              Konfirmasi & Impor {{ preview.created }} Alumni
            </Button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
