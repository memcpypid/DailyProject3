<script setup>
import { ref, watch, computed } from 'vue';
import { X } from 'lucide-vue-next';
import { useAlumniStore } from '@/stores/alumni';
import Input from '@/components/ui/Input.vue';
import Button from '@/components/ui/Button.vue';

const props = defineProps({
  isOpen: { type: Boolean, required: true },
  alumni: { type: Object, default: null }, // null = create mode
});

const emit = defineEmits(['close', 'success']);
const alumniStore = useAlumniStore();
const errorMsg = ref('');
const isSubmitting = ref(false);

const isEditMode = computed(() => !!props.alumni);
const title = computed(() => (isEditMode.value ? 'Edit Alumni' : 'Tambah Alumni'));

const emptyForm = () => ({
  full_name: '',
  nim: '',
  tahun_masuk: '',
  tanggal_lulus: '',
  fakultas: '',
  program_studi: '',
  name_variations: '',
});

const formData = ref(emptyForm());

watch(
  () => props.isOpen,
  (open) => {
    if (!open) return;
    errorMsg.value = '';
    if (props.alumni) {
      formData.value = {
        full_name: props.alumni.full_name,
        nim: props.alumni.nim,
        tahun_masuk: props.alumni.tahun_masuk ?? '',
        tanggal_lulus: props.alumni.tanggal_lulus || '',
        fakultas: props.alumni.fakultas,
        program_studi: props.alumni.program_studi,
        name_variations: (props.alumni.name_variations || []).join(', '),
      };
    } else {
      formData.value = emptyForm();
    }
  }
);

const handleSubmit = async () => {
  errorMsg.value = '';
  isSubmitting.value = true;
  try {
    const payload = {
      ...formData.value,
      tahun_masuk: formData.value.tahun_masuk ? Number(formData.value.tahun_masuk) : null,
      tanggal_lulus: formData.value.tanggal_lulus || null,
      name_variations: formData.value.name_variations
        .split(',')
        .map((v) => v.trim())
        .filter(Boolean),
    };
    if (isEditMode.value) {
      await alumniStore.update(props.alumni.id, payload);
    } else {
      await alumniStore.create(payload);
    }
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
  <div v-if="isOpen" class="fixed inset-0 z-50 overflow-y-auto" aria-labelledby="modal-title" role="dialog"
    aria-modal="true">
    <div class="fixed inset-0 bg-black/10 transition-opacity backdrop-blur-sm" @click="!isSubmitting && emit('close')"
      aria-hidden="true"></div>

    <div class="flex min-h-screen items-end justify-center p-4 text-center sm:items-center sm:p-0">
      <div
        class="relative transform overflow-hidden rounded-lg bg-card text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-lg border border-border"
        @click.stop>
        <div class="bg-card px-4 pb-4 pt-5 sm:p-6">
          <div class="flex justify-between items-center mb-5">
            <h3 class="text-lg font-semibold leading-6 text-foreground" id="modal-title">{{ title }}</h3>
            <button @click="emit('close')" :disabled="isSubmitting" class="text-muted-foreground hover:text-foreground">
              <X class="w-5 h-5" />
            </button>
          </div>

          <div v-if="errorMsg" class="mb-4 p-3 text-sm bg-rose-500/10 text-rose-500 border border-rose-500/20 rounded-lg">
            {{ errorMsg }}
          </div>

          <form @submit.prevent="handleSubmit" class="space-y-4">
            <Input id="full_name" v-model="formData.full_name" label="Nama Lulusan" required placeholder="Muhammad Rizky" />

            <div class="grid grid-cols-2 gap-4">
              <Input id="nim" v-model="formData.nim" label="NIM" placeholder="201910370001" />
              <Input id="tahun_masuk" v-model="formData.tahun_masuk" type="number" label="Tahun Masuk" placeholder="2016" />
            </div>

            <Input id="tanggal_lulus" v-model="formData.tanggal_lulus" type="date" label="Tanggal Lulus" />

            <div class="grid grid-cols-2 gap-4">
              <Input id="fakultas" v-model="formData.fakultas" label="Fakultas" placeholder="Teknik" />
              <Input id="program_studi" v-model="formData.program_studi" label="Program Studi" placeholder="Informatika" />
            </div>

            <Input id="name_variations" v-model="formData.name_variations" label="Variasi Nama"
              placeholder="M. Rizky, Rizky M. (pisahkan dengan koma)"
              help-text="Variasi penulisan nama untuk membantu pencocokan identitas." />

            <div class="pt-4 flex justify-end gap-3 border-t border-border mt-6">
              <Button type="button" variant="outline" @click="emit('close')" :disabled="isSubmitting" customClass="w-full sm:w-auto">
                Batal
              </Button>
              <Button type="submit" :loading="isSubmitting" customClass="w-full sm:w-auto">
                {{ isEditMode ? 'Simpan Perubahan' : 'Tambah Alumni' }}
              </Button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>
