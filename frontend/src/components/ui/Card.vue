<script setup>
defineProps({
  customClass: {
    type: String,
    default: ''
  },
  bodyClass: {
    type: String,
    default: 'p-6'
  },
  headerClass: {
    type: String,
    default: 'p-6 pb-0'
  }
});
</script>

<template>
  <div class="rounded-xl border border-border bg-card text-card-foreground shadow-sm overflow-hidden" :class="customClass">
    <div v-if="$slots.header" :class="headerClass">
      <slot name="header"></slot>
    </div>
    
    <div :class="bodyClass">
      <slot></slot>
    </div>
    
    <div v-if="$slots.footer" class="p-6 pt-0">
      <slot name="footer"></slot>
    </div>
  </div>
</template>
