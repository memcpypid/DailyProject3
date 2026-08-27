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
  type: {
    type: String,
    default: 'text'
  },
  placeholder: {
    type: String,
    default: ''
  },
  required: {
    type: Boolean,
    default: false
  },
  disabled: {
    type: Boolean,
    default: false
  },
  readonly: {
    type: Boolean,
    default: false
  },
  helpText: {
    type: String,
    default: ''
  },
  error: {
    type: String,
    default: ''
  },
  inputClass: {
    type: String,
    default: ''
  }
});

const emit = defineEmits(['update:modelValue']);

const computedInputClasses = computed(() => {
  const base = "flex h-10 w-full rounded-md border bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 transition-colors";
  const state = props.error 
    ? "border-rose-500 focus-visible:ring-rose-500" 
    : "border-input focus-visible:ring-primary";
    
  return [base, state, props.inputClass].join(' ');
});
</script>

<template>
  <div class="space-y-2 w-full">
    <div v-if="label || $slots['label-extra']" class="flex items-center justify-between">
      <label :for="id" class="text-sm font-medium leading-none text-foreground" :class="{'text-rose-500': error}">
        {{ label }} <span v-if="required" class="text-rose-500">*</span>
      </label>
      <slot name="label-extra"></slot>
    </div>
    
    <div class="relative">
      <slot name="icon-left"></slot>
      <input
        :id="id"
        :type="type"
        :value="modelValue"
        @input="emit('update:modelValue', $event.target.value)"
        :required="required"
        :disabled="disabled"
        :readonly="readonly"
        :placeholder="placeholder"
        :class="[computedInputClasses, { 'pl-9': !!$slots['icon-left'] }]"
      />
    </div>
    
    <p v-if="error" class="text-xs text-rose-500 font-medium">{{ error }}</p>
    <p v-else-if="helpText" class="text-xs text-muted-foreground">{{ helpText }}</p>
  </div>
</template>
