<script setup>
import { computed } from 'vue';
import { Loader2 } from 'lucide-vue-next';

const props = defineProps({
  variant: {
    type: String,
    default: 'primary', // primary, secondary, danger, ghost, outline
    validator: (value) => ['primary', 'secondary', 'danger', 'ghost', 'outline'].includes(value)
  },
  size: {
    type: String,
    default: 'default', // default, sm, lg, icon
    validator: (value) => ['default', 'sm', 'lg', 'icon'].includes(value)
  },
  loading: {
    type: Boolean,
    default: false
  },
  disabled: {
    type: Boolean,
    default: false
  },
  type: {
    type: String,
    default: 'button'
  },
  customClass: {
    type: String,
    default: ''
  }
});

const emit = defineEmits(['click']);

const computedClasses = computed(() => {
  const base = "inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none";
  
  const variants = {
    primary: "bg-primary text-primary-foreground hover:bg-primary-hover shadow hover:shadow-md",
    secondary: "bg-secondary text-secondary-foreground hover:bg-secondary/80",
    danger: "bg-rose-500 text-white hover:bg-rose-600 shadow hover:shadow-md",
    ghost: "hover:bg-accent hover:text-accent-foreground",
    outline: "border border-input bg-background hover:bg-accent hover:text-accent-foreground shadow-sm"
  };

  const sizes = {
    default: "h-10 py-2 px-4",
    sm: "h-9 px-3",
    lg: "h-11 px-8 rounded-md",
    icon: "h-10 w-10"
  };

  return [base, variants[props.variant], sizes[props.size], props.customClass].join(' ');
});

const handleClick = (e) => {
  if (!props.loading && !props.disabled) {
    emit('click', e);
  }
};
</script>

<template>
  <button :type="type" :disabled="disabled || loading" :class="computedClasses" @click="handleClick">
    <Loader2 v-if="loading" class="w-4 h-4 mr-2 animate-spin" :class="{'mr-0': size === 'icon' && !$slots.default}" />
    <slot name="icon-left" v-else-if="!loading"></slot>
    <slot></slot>
  </button>
</template>
