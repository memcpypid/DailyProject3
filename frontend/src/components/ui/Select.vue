<script setup>
import { computed } from 'vue';

const props = defineProps({
  modelValue: {
    type: [String, Number],
    default: ''
  },
  id: {
    type: String,
    required: true
  },
  label: {
    type: String,
    default: ''
  },
  options: {
    type: Array,
    default: () => [] // [{label: 'User', value: 'user'}]
  },
  required: {
    type: Boolean,
    default: false
  },
  disabled: {
    type: Boolean,
    default: false
  },
  error: {
    type: String,
    default: ''
  }
});

const emit = defineEmits(['update:modelValue']);

const computedSelectClasses = computed(() => {
  const base = "flex h-10 w-full rounded-md border bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 transition-colors cursor-pointer appearance-none";
  const state = props.error 
    ? "border-rose-500 focus-visible:ring-rose-500" 
    : "border-input focus-visible:ring-primary";
    
  return [base, state].join(' ');
});
</script>

<template>
  <div class="space-y-1 w-full">
    <label v-if="label" :for="id" class="text-sm font-medium leading-none text-foreground" :class="{'text-rose-500': error}">
      {{ label }} <span v-if="required" class="text-rose-500">*</span>
    </label>
    
    <div class="relative">
      <select
        :id="id"
        :value="modelValue"
        @change="emit('update:modelValue', $event.target.value)"
        :required="required"
        :disabled="disabled"
        :class="computedSelectClasses"
      >
        <slot>
          <option v-for="opt in options" :key="opt.value" :value="opt.value">
            {{ opt.label }}
          </option>
        </slot>
      </select>
      
      <!-- Custom Arrow -->
      <div class="pointer-events-none absolute inset-y-0 right-0 flex items-center px-3 text-muted-foreground">
        <svg class="h-4 w-4 fill-current" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20">
          <path d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z"/>
        </svg>
      </div>
    </div>
    
    <p v-if="error" class="text-xs text-rose-500 font-medium">{{ error }}</p>
  </div>
</template>
