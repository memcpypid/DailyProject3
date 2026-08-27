<script setup>
import { ref, watch, onMounted } from 'vue';
import { X } from 'lucide-vue-next';
import { useAlumniStore } from '@/stores/alumni';
import { useSourceStore } from '@/stores/sources';
import Input from '@/components/ui/Input.vue';
import Select from '@/components/ui/Select.vue';
import Button from '@/components/ui/Button.vue';

const props = defineProps({
  isOpen: { type: Boolean, required: true },
  alumniId: { type: String, required: true },
  initialData: { type: Object, default: null },
});

const emit = defineEmits(['close', 'success']);
const alumniStore = useAlumniStore();
const sourceStore = useSourceStore();
const errorMsg = ref('');
const isSubmitting = ref(false);

onMounted(() => {
  if (!sourceStore.items.length) sourceStore.fetchList();
});

const employmentOptions = [
  { value: '', label: 'Pilih jenis pekerjaan' },
  { value: 'PNS', label: 'PNS' },
  { value: 'Swasta', label: 'Swasta' },
  { value: 'Wirausaha', label: 'Wirausaha' },
];

const emptyForm = () => ({
  source_id: '',
  raw_name: '',
  linkedin_url: '',
  instagram_url: '',
  facebook_url: '',
  tiktok_url: '',
  email: '',
  phone: '',
  employer_name: '',
  employer_address: '',
  position: '',
  employment_type: '',
  employer_social_media: '',
  snippet: '',
});

const formData = ref(emptyForm());

watch(
  () => props.isOpen,
  (open) => {
    if (!open) return;
    errorMsg.value = '';
    formData.value = { ...emptyForm(), ...(props.initialData || {}) };
    if (sourceStore.items.length && !formData.value.source_id) {
      formData.value.source_id = sourceStore.items[0].id;
    }
  }
);

const handleSubmit = async () => {
  errorMsg.value = '';
  if (!formData.value.source_id) {
    errorMsg.value = 'Pilih sumber temuan terlebih dahulu.';
    return;
  }
  isSubmitting.value = true;
  try {
    await alumniStore.addManualCandidate(props.alumniId, formData.value);
    emit('success');
    emit('close');
  } catch (err) {
    errorMsg.value = err.response?.data?.detail || err.message || 'Operasi gagal';
  } finally {
    isSubmitting.value = false;
  }
};
</script>

<template>
  <div v-if="isOpen" class="fixed inset-0 z-50 overflow-y-auto" role="dialog" aria-modal="true">
    <div class="fixed inset-0 bg-black/10 backdrop-blur-sm" @click="!isSubmitting && emit('close')"></div>

    <div class="flex min-h-screen items-end justify-center p-4 text-center sm:items-center sm:p-0">
      <div class="relative overflow-hidden rounded-lg bg-card text-left shadow-xl sm:my-8 sm:w-full sm:max-w-2xl border border-border" @click.stop>
        <div class="px-4 pb-4 pt-5 sm:p-6 max-h-[85vh] overflow-y-auto">
          <div class="flex justify-between items-center mb-2">
            <h3 class="text-lg font-semibold text-foreground">Input Temuan Manual</h3>
            <button @click="emit('close')" :disabled="isSubmitting" class="text-muted-foreground hover:text-foreground">
              <X class="w-5 h-5" />
            </button>
          </div>
          <p class="text-xs text-muted-foreground mb-5">
            Untuk data yang benar-benar sudah Anda verifikasi sendiri satu per satu (bukan hasil simulasi).
          </p>
          <div v-if="initialData" class="mb-4 p-3 text-xs bg-amber-500/10 text-amber-500 border border-amber-500/20 rounded-lg">
            Terisi otomatis dari hasil pencarian web. Periksa dan sesuaikan tiap kolom sebelum disimpan -
            pastikan ini benar-benar orang yang sama.
          </div>

          <div v-if="errorMsg" class="mb-4 p-3 text-sm bg-rose-500/10 text-rose-500 border border-rose-500/20 rounded-lg">
            {{ errorMsg }}
          </div>

          <form @submit.prevent="handleSubmit" class="space-y-4">
            <div class="grid grid-cols-2 gap-4">
              <Select id="source_id" v-model="formData.source_id" label="Sumber Temuan" required
                :options="sourceStore.items.map((s) => ({ value: s.id, label: s.name }))" />
              <Input id="raw_name" v-model="formData.raw_name" label="Nama yang Ditemukan" placeholder="Muhammad Rizky" />
            </div>

            <p class="text-xs font-medium text-muted-foreground pt-2">1. Alamat Sosial Media</p>
            <div class="grid grid-cols-2 gap-4">
              <Input id="linkedin_url" v-model="formData.linkedin_url" label="LinkedIn" placeholder="https://linkedin.com/in/..." />
              <Input id="instagram_url" v-model="formData.instagram_url" label="Instagram" placeholder="https://instagram.com/..." />
              <Input id="facebook_url" v-model="formData.facebook_url" label="Facebook" placeholder="https://facebook.com/..." />
              <Input id="tiktok_url" v-model="formData.tiktok_url" label="TikTok" placeholder="https://tiktok.com/@..." />
            </div>

            <p class="text-xs font-medium text-muted-foreground pt-2">2-3. Kontak</p>
            <div class="grid grid-cols-2 gap-4">
              <Input id="email" v-model="formData.email" type="email" label="Email" />
              <Input id="phone" v-model="formData.phone" label="No. HP" placeholder="08xxxxxxxxxx" />
            </div>

            <p class="text-xs font-medium text-muted-foreground pt-2">4-7. Pekerjaan</p>
            <div class="grid grid-cols-2 gap-4">
              <Input id="employer_name" v-model="formData.employer_name" label="Tempat Bekerja" />
              <Input id="employer_address" v-model="formData.employer_address" label="Alamat Bekerja" />
              <Input id="position" v-model="formData.position" label="Posisi" placeholder="Software Engineer" />
              <Select id="employment_type" v-model="formData.employment_type" label="Jenis Pekerjaan" :options="employmentOptions" />
            </div>

            <p class="text-xs font-medium text-muted-foreground pt-2">8. Sosial Media Tempat Bekerja</p>
            <Input id="employer_social_media" v-model="formData.employer_social_media" placeholder="https://instagram.com/perusahaan" />

            <Input id="snippet" v-model="formData.snippet" label="Catatan (opsional)" placeholder="Sumber/keterangan tambahan" />

            <div class="pt-4 flex justify-end gap-3 border-t border-border mt-6">
              <Button type="button" variant="outline" @click="emit('close')" :disabled="isSubmitting" customClass="w-full sm:w-auto">Batal</Button>
              <Button type="submit" :loading="isSubmitting" customClass="w-full sm:w-auto">Simpan Temuan</Button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>
