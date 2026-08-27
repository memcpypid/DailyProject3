<script setup>
import ToastContainer from './components/ui/ToastContainer.vue';
import { onMounted } from 'vue';
import { healthCheck } from './services/api';

onMounted(() => {
  healthCheck();
});
</script>

<template>
  <router-view />
  <ToastContainer />
</template>
