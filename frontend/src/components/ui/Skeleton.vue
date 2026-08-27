<script setup>
import { computed } from 'vue';

const props = defineProps({
  customClass: {
    type: String,
    default: ''
  },
  width: {
    type: String,
    default: '100%'
  },
  height: {
    type: String,
    default: '1rem'
  },
  circle: {
    type: Boolean,
    default: false
  }
});

const computedStyles = computed(() => {
  return {
    width: props.width,
    height: props.height,
    borderRadius: props.circle ? '50%' : '0.375rem'
  };
});
</script>

<template>
  <div 
    class="animate-pulse bg-muted rounded-md" 
    :class="customClass"
    :style="computedStyles"
  ></div>
</template>
