<script setup>
import { ref, watch, computed } from 'vue';
import { X } from 'lucide-vue-next';
import { useSourceStore } from '@/stores/sources';
import Input from '@/components/ui/Input.vue';
import Button from '@/components/ui/Button.vue';

const props = defineProps({
  isOpen: { type: Boolean, required: true },
  source: { type: Object, default: null },
});

const emit = defineEmits(['close', 'success']);
const sourceStore = useSourceStore();
const errorMsg = ref('');
const isSubmitting = ref(false);

const isEditMode = computed(() => !!props.source);

const emptyForm = () => ({ name: '', access_type: '', weight: 0.5 });
const formData = ref(emptyForm());

watch(
  () => props.isOpen,
  (open) => {
    if (!open) return;
    errorMsg.value = '';
    formData.value = props.source
      ? { name: props.source.name, access_type: props.source.access_type, weight: props.source.weight }
      : emptyForm();
  }
);

const handleSubmit = async () => {
  errorMsg.value = '';
  isSubmitting.value = true;
  try {
    const payload = { ...formData.value, weight: Number(formData.value.weight) };
    if (isEditMode.value) {
      await sourceStore.update(props.source.id, payload);
    } else {
      await sourceStore.create(payload);
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
  <div v-if="isOpen" class="fixed inset-0 z-50 overflow-y-auto" role="dialog" aria-modal="true">
    <div class="fixed inset-0 bg-black/10 backdrop-blur-sm" @click="!isSubmitting && emit('close')"></div>
    <div class="flex min-h-screen items-end justify-center p-4 text-center sm:items-center sm:p-0">
      <div class="relative overflow-hidden rounded-lg bg-card text-left shadow-xl sm:my-8 sm:w-full sm:max-w-md border border-border" @click.stop>
        <div class="px-4 pb-4 pt-5 sm:p-6">
          <div class="flex justify-between items-center mb-5">
            <h3 class="text-lg font-semibold text-foreground">{{ isEditMode ? 'Edit Sumber Data' : 'Tambah Sumber Data' }}</h3>
            <button @click="emit('close')" :disabled="isSubmitting" class="text-muted-foreground hover:text-foreground">
              <X class="w-5 h-5" />
            </button>
          </div>

          <div v-if="errorMsg" class="mb-4 p-3 text-sm bg-rose-500/10 text-rose-500 border border-rose-500/20 rounded-lg">
            {{ errorMsg }}
          </div>

          <form @submit.prevent="handleSubmit" class="space-y-4">
            <Input id="name" v-model="formData.name" label="Nama Sumber" required placeholder="mis. Google Scholar" />
            <Input id="access_type" v-model="formData.access_type" label="Cara Akses" placeholder="mis. Parsing profil publik" />
            <Input id="weight" v-model="formData.weight" type="number" label="Bobot Kepercayaan (0-1)" required
              help-text="Catatan referensi seberapa bisa dipercaya sumber ini - bersifat informasional saja, tidak memengaruhi apa pun secara otomatis." />

            <div class="pt-4 flex justify-end gap-3 border-t border-border mt-6">
              <Button type="button" variant="outline" @click="emit('close')" :disabled="isSubmitting" customClass="w-full sm:w-auto">Batal</Button>
              <Button type="submit" :loading="isSubmitting" customClass="w-full sm:w-auto">Simpan</Button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>
