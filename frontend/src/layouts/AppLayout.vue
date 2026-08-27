<script setup>
import { useAuthStore } from '@/stores/auth';
import { useThemeStore } from '@/stores/theme';
import { LogOut, Sun, Moon, LayoutDashboard, Users, Database, UserCog, Menu, X } from 'lucide-vue-next';
import { ref } from 'vue';

const authStore = useAuthStore();
const themeStore = useThemeStore();
const mobileOpen = ref(false);

const logout = () => {
  authStore.logout();
};

const navItems = [
  { to: '/app/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/app/alumni', label: 'Alumni', icon: Users },
  { to: '/app/sources', label: 'Sumber Data', icon: Database },
  { to: '/app/profile', label: 'Profil', icon: UserCog },
];
</script>

<template>
  <div class="min-h-screen bg-background text-foreground flex transition-colors duration-300">
    <!-- Sidebar (desktop) -->
    <aside class="w-64 bg-card border-r border-border hidden md:flex flex-col">
      <div class="p-6">
        <h2 class="text-xl font-bold text-primary leading-tight">Pelacakan Alumni</h2>
        <p class="text-xs text-muted-foreground mt-1">Multi-Sumber</p>
      </div>
      <nav class="flex-1 px-4 space-y-2">
        <router-link v-for="item in navItems" :key="item.to" :to="item.to"
          class="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-secondary hover:text-primary transition-colors"
          active-class="bg-secondary text-primary font-medium">
          <component :is="item.icon" class="w-5 h-5" /> {{ item.label }}
        </router-link>
      </nav>
      <div class="p-4 border-t border-border">
        <div class="text-sm text-muted-foreground mb-4 px-2">
          Masuk sebagai <br><span class="font-semibold text-foreground">{{ authStore.user?.name }}</span>
        </div>
        <button @click="logout"
          class="w-full flex items-center justify-center gap-2 px-4 py-2 bg-rose-500 text-white rounded-lg hover:bg-rose-600 transition-colors">
          <LogOut class="w-4 h-4" /> Keluar
        </button>
      </div>
    </aside>

    <!-- Sidebar (mobile) -->
    <div v-if="mobileOpen" class="fixed inset-0 z-40 md:hidden">
      <div class="fixed inset-0 bg-black/40" @click="mobileOpen = false"></div>
      <aside class="relative w-64 h-full bg-card border-r border-border flex flex-col">
        <div class="p-6 flex items-center justify-between">
          <h2 class="text-xl font-bold text-primary">Pelacakan Alumni</h2>
          <button @click="mobileOpen = false" class="text-muted-foreground"><X class="w-5 h-5" /></button>
        </div>
        <nav class="flex-1 px-4 space-y-2">
          <router-link v-for="item in navItems" :key="item.to" :to="item.to" @click="mobileOpen = false"
            class="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-secondary hover:text-primary transition-colors"
            active-class="bg-secondary text-primary font-medium">
            <component :is="item.icon" class="w-5 h-5" /> {{ item.label }}
          </router-link>
        </nav>
        <div class="p-4 border-t border-border">
          <button @click="logout"
            class="w-full flex items-center justify-center gap-2 px-4 py-2 bg-rose-500 text-white rounded-lg hover:bg-rose-600 transition-colors">
            <LogOut class="w-4 h-4" /> Keluar
          </button>
        </div>
      </aside>
    </div>

    <!-- Main Content -->
    <div class="flex-1 flex flex-col min-w-0">
      <!-- Navbar -->
      <header class="h-16 bg-card border-b border-border flex items-center justify-between px-4 sm:px-6">
        <button class="md:hidden p-2 rounded-lg hover:bg-secondary text-foreground" @click="mobileOpen = true">
          <Menu class="w-6 h-6" />
        </button>
        <div class="flex-1"></div>
        <button @click="themeStore.toggleDark()" class="p-2 rounded-full hover:bg-secondary transition-colors">
          <Moon v-if="!themeStore.isDark" class="w-5 h-5 text-foreground" />
          <Sun v-else class="w-5 h-5 text-yellow-400" />
        </button>
      </header>

      <!-- Page Content -->
      <main class="flex-1 p-4 sm:p-6 lg:p-8 overflow-y-auto">
        <router-view v-slot="{ Component, route }">
          <transition name="fade" mode="out-in">
            <component :is="Component" :key="route.fullPath" />
          </transition>
        </router-view>
      </main>
    </div>
  </div>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
