<script setup>
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-background text-foreground flex-col">
    <h1 class="text-7xl font-bold text-primary mb-4">404</h1>
    <h2 class="text-2xl font-semibold mb-6">Page Not Found</h2>
    <p class="text-muted-foreground mb-8 text-center max-w-md">
      The page you are looking for doesn't exist or has been moved.
    </p>
    <router-link to="/" class="px-6 py-3 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary-hover transition-colors">
      Go back home
    </router-link>
  </div>
</template>
