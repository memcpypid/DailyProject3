<script setup>
import { computed } from 'vue';

const props = defineProps({
  variant: {
    type: String,
    default: 'default', // default, success, warning, danger, info, outline
    validator: (value) => ['default', 'success', 'warning', 'danger', 'info', 'outline'].includes(value)
  },
  customClass: {
    type: String,
    default: ''
  }
});

const computedClasses = computed(() => {
  const base = "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2";
  
  const variants = {
    default: "bg-primary/10 text-primary border-transparent",
    success: "bg-emerald-500/10 text-emerald-500 border-transparent",
    warning: "bg-amber-500/10 text-amber-500 border-transparent",
    danger: "bg-rose-500/10 text-rose-500 border-transparent",
    info: "bg-blue-500/10 text-blue-500 border-transparent",
    outline: "text-foreground border border-border"
  };

  return [base, variants[props.variant], props.customClass].join(' ');
});
</script>

<template>
  <div :class="computedClasses">
    <slot></slot>
  </div>
</template>
