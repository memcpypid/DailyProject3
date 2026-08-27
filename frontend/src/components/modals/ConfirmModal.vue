<script setup>
import { computed } from 'vue';
import { AlertTriangle, Info } from 'lucide-vue-next';
import Button from '@/components/ui/Button.vue';

const props = defineProps({
  isOpen: {
    type: Boolean,
    required: true
  },
  title: {
    type: String,
    default: 'Confirm Action'
  },
  message: {
    type: String,
    default: 'Are you sure you want to perform this action?'
  },
  confirmText: {
    type: String,
    default: 'Confirm'
  },
  cancelText: {
    type: String,
    default: 'Cancel'
  },
  type: {
    type: String,
    default: 'danger', // 'danger', 'warning', 'info'
    validator: (value) => ['danger', 'warning', 'info'].includes(value)
  },
  isLoading: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['close', 'confirm']);

// Computed styles based on type
const iconStyle = computed(() => {
  if (props.type === 'danger') return 'bg-rose-500/10 text-rose-500';
  if (props.type === 'warning') return 'bg-amber-500/10 text-amber-500';
  return 'bg-blue-500/10 text-blue-500';
});

const buttonVariant = computed(() => {
  if (props.type === 'danger') return 'danger';
  return 'primary'; 
});
</script>

<template>
  <div v-if="isOpen" class="fixed inset-0 z-50 overflow-y-auto" aria-labelledby="modal-title" role="dialog"
    aria-modal="true">
    <!-- Backdrop overlay -->
    <div class="fixed inset-0 bg-black/10 bg-opacity-100 transition-opacity backdrop-blur-sm"
      @click="!isLoading && emit('close')" aria-hidden="true"></div>

    <!-- Modal Panel -->
    <div class="flex min-h-screen items-end justify-center p-4 text-center sm:items-center sm:p-0">
      <div
        class="relative transform overflow-hidden rounded-lg bg-card text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-lg border border-border"
        @click.stop>
        <div class="bg-card px-4 pb-4 pt-5 sm:p-6 sm:pb-4">
          <div class="sm:flex sm:items-start">
            <!-- Icon -->
            <div class="mx-auto flex h-12 w-12  items-center justify-center rounded-full sm:mx-0 sm:h-10 sm:w-10"
              :class="iconStyle">
              <AlertTriangle v-if="type === 'danger' || type === 'warning'" class="h-6 w-6" aria-hidden="true" />
              <Info v-else class="h-6 w-6" aria-hidden="true" />
            </div>

            <div class="mt-3 text-center sm:ml-4 sm:mt-0 sm:text-left">
              <h3 class="text-lg font-semibold leading-6 text-foreground" id="modal-title">
                {{ title }}
              </h3>
              <div class="mt-2">
                <p class="text-sm text-muted-foreground whitespace-pre-wrap">
                  {{ message }}
                </p>
              </div>
            </div>
          </div>
        </div>

        <div class="bg-muted/50 px-4 py-3 sm:flex sm:flex-row-reverse sm:gap-3 sm:px-6">
          <Button 
            type="button" 
            :variant="buttonVariant" 
            :loading="isLoading" 
            @click="emit('confirm')"
            customClass="w-full sm:w-auto"
          >
            {{ confirmText }}
          </Button>
          
          <Button 
            type="button" 
            variant="ghost" 
            :disabled="isLoading" 
            @click="emit('close')"
            customClass="w-full sm:w-auto mt-3 sm:mt-0"
          >
            {{ cancelText }}
          </Button>
        </div>
      </div>
    </div>
  </div>
</template>
