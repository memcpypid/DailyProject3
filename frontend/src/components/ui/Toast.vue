<script setup>
import { computed } from 'vue';
import { 
  CheckCircle, 
  AlertCircle, 
  AlertTriangle, 
  Info, 
  X 
} from 'lucide-vue-next';

const props = defineProps({
  toast: {
    type: Object,
    required: true
  }
});

const emit = defineEmits(['close']);

const icon = computed(() => {
  switch (props.toast.type) {
    case 'success': return CheckCircle;
    case 'error': return AlertCircle;
    case 'warning': return AlertTriangle;
    default: return Info;
  }
});

const styles = computed(() => {
  switch (props.toast.type) {
    case 'success': return 'bg-emerald-50 text-emerald-800 border-emerald-200 dark:bg-emerald-900/30 dark:text-emerald-400 dark:border-emerald-800/50';
    case 'error': return 'bg-rose-50 text-rose-800 border-rose-200 dark:bg-rose-900/30 dark:text-rose-400 dark:border-rose-800/50';
    case 'warning': return 'bg-amber-50 text-amber-800 border-amber-200 dark:bg-amber-900/30 dark:text-amber-400 dark:border-amber-800/50';
    default: return 'bg-blue-50 text-blue-800 border-blue-200 dark:bg-blue-900/30 dark:text-blue-400 dark:border-blue-800/50';
  }
});

const iconStyle = computed(() => {
  switch (props.toast.type) {
    case 'success': return 'text-emerald-500';
    case 'error': return 'text-rose-500';
    case 'warning': return 'text-amber-500';
    default: return 'text-blue-500';
  }
});
</script>

<template>
  <div 
    class="flex items-center gap-3 p-4 rounded-lg border shadow-lg max-w-sm w-full pointer-events-auto transition-all duration-300"
    :class="styles"
  >
    <component :is="icon" class="w-5 h-5 shrink-0" :class="iconStyle" />
    <span class="text-sm font-medium flex-1">{{ toast.message }}</span>
    <button 
      @click="emit('close')" 
      class="p-1 rounded-md hover:bg-black/5 dark:hover:bg-white/5 transition-colors"
    >
      <X class="w-4 h-4 opacity-50 hover:opacity-100" />
    </button>
  </div>
</template>
