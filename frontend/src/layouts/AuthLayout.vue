<script setup>
</script>

<template>
  <div class="relative min-h-screen flex items-center justify-center p-4 sm:p-6 transition-colors duration-300">
    <!-- Animated background elements (subtle) -->
    <div class="absolute inset-0 z-0 overflow-hidden bg-background">
      <div class="absolute top-[20%] left-[10%] w-72 h-72 bg-primary/10 rounded-full mix-blend-multiply filter blur-3xl opacity-70 animate-pulse-slow"></div>
      <div class="absolute bottom-[20%] right-[10%] w-72 h-72 bg-secondary/30 dark:bg-primary/5 rounded-full mix-blend-multiply filter blur-3xl opacity-70 animate-pulse-slow" style="animation-delay: 1.5s;"></div>
    </div>
    
    <div class="relative z-10 w-full max-w-md bg-card/90 backdrop-blur-xl text-card-foreground shadow-2xl rounded-2xl border border-border/50 overflow-hidden animate-fade-in-up">
      <router-view v-slot="{ Component }">
        <transition 
          enter-active-class="transition duration-300 ease-out"
          enter-from-class="opacity-0 translate-y-4"
          enter-to-class="opacity-100 translate-y-0"
          leave-active-class="transition duration-200 ease-in"
          leave-from-class="opacity-100"
          leave-to-class="opacity-0"
          mode="out-in"
        >
          <component :is="Component" />
        </transition>
      </router-view>
    </div>
  </div>
</template>
