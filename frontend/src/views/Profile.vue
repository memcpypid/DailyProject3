<script setup>
import { onMounted } from 'vue';
import { Save } from 'lucide-vue-next';
import { useAuthStore } from '@/stores/auth';
import Input from '@/components/ui/Input.vue';
import Button from '@/components/ui/Button.vue';

const authStore = useAuthStore();

onMounted(() => {
  authStore.initProfileForm();
});

const handleSave = async () => {
  await authStore.updateProfile();
};
</script>

<template>
  <div class="max-w-2xl mx-auto space-y-6">
    <div class="mb-8">
      <h1 class="text-3xl font-bold tracking-tight text-foreground">Profil Saya</h1>
      <p class="text-muted-foreground mt-2">Kelola informasi akun Anda.</p>
    </div>

    <div class="bg-card border border-border shadow-sm rounded-xl overflow-hidden">
      <div class="p-6 sm:p-8 space-y-6">
        <div class="flex items-center gap-6">
          <div
            class="w-20 h-20 bg-primary/10 text-primary rounded-full flex items-center justify-center text-3xl font-bold border border-primary/20">
            {{ authStore.user?.name?.charAt(0) || 'U' }}
          </div>
          <div>
            <h2 class="text-xl font-semibold text-foreground">{{ authStore.user?.name }}</h2>
            <p class="text-muted-foreground">{{ authStore.user?.email }}</p>
          </div>
        </div>

        <div class="border-t border-border pt-6">
          <h3 class="text-lg font-medium text-foreground mb-4">Informasi Pribadi</h3>
          <form class="space-y-4" @submit.prevent="handleSave">
            <Input
              id="name"
              v-model="authStore.profileForm.name"
              label="Nama Lengkap"
              required
            />

            <Input
              id="email"
              :model-value="authStore.user?.email"
              label="Email"
              readonly
            />

            <Input
              id="password"
              v-model="authStore.profileForm.password"
              type="password"
              label="Password"
              placeholder="Kosongkan jika tidak ingin mengubah password"
            />

            <div class="pt-4 flex justify-end">
              <Button type="submit" :loading="authStore.loading">
                <template #icon-left><Save class="w-4 h-4 mr-2" /></template>
                {{ authStore.loading ? 'Menyimpan...' : 'Simpan Perubahan' }}
              </Button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>
