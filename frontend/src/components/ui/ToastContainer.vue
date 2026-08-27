<script setup>
import { useToast } from '@/composables/useToast';
import Toast from './Toast.vue';

const { toasts, removeToast } = useToast();
</script>

<template>
  <div class="fixed top-4 right-4 z-50 flex flex-col gap-2 pointer-events-none w-full max-w-sm sm:items-end">
    <TransitionGroup name="toast" enter-from-class="translate-x-full opacity-0"
      enter-active-class="transition duration-300 ease-out" enter-to-class="translate-x-0 opacity-100"
      leave-from-class="translate-x-0 opacity-100" leave-active-class="transition duration-300 ease-in absolute"
      leave-to-class="translate-x-full opacity-0" move-class="transition duration-300 ease-in-out">
      <Toast v-for="toast in toasts" :key="toast.id" :toast="toast" @close="removeToast(toast.id)" />
    </TransitionGroup>
  </div>
</template>

<style scoped>
.toast-leave-active {
  position: absolute;
}
</style>
