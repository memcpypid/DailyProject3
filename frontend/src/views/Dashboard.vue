<script setup>
import { onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { Users, CheckCircle2, Database, UserPlus } from 'lucide-vue-next';
import { useDashboardStore } from '@/stores/dashboard';
import Card from '@/components/ui/Card.vue';
import Button from '@/components/ui/Button.vue';
import Skeleton from '@/components/ui/Skeleton.vue';

const dashboardStore = useDashboardStore();
const router = useRouter();

onMounted(() => {
  dashboardStore.fetchStats();
});

const statCards = [
  { key: 'belum_dilacak', label: 'Belum Dilacak', icon: Users, color: 'text-muted-foreground' },
  { key: 'terverifikasi_manual', label: 'Terverifikasi (Manual)', icon: CheckCircle2, color: 'text-emerald-500' },
];

const formatDate = (iso) => new Date(iso).toLocaleString('id-ID', { dateStyle: 'medium', timeStyle: 'short' });
</script>

<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h1 class="text-3xl font-bold tracking-tight text-foreground">Dashboard</h1>
        <p class="text-muted-foreground mt-2">Ringkasan pelacakan alumni dari berbagai sumber publik.</p>
      </div>
      <div class="flex gap-3">
        <Button variant="outline" @click="router.push('/app/alumni')">
          <template #icon-left><UserPlus class="w-4 h-4 mr-2" /></template>
          Kelola Alumni
        </Button>
      </div>
    </div>

    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <template v-if="dashboardStore.loading && !dashboardStore.stats">
        <Skeleton v-for="i in 2" :key="i" height="6rem" custom-class="rounded-xl" />
      </template>
      <Card v-else v-for="card in statCards" :key="card.key" body-class="p-6">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-muted-foreground">{{ card.label }}</p>
            <p class="text-3xl font-bold text-foreground mt-1">
              {{ dashboardStore.stats?.status_breakdown?.[card.key] ?? 0 }}
            </p>
          </div>
          <component :is="card.icon" class="w-8 h-8" :class="card.color" />
        </div>
      </Card>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <Card custom-class="lg:col-span-1">
        <template #header>
          <h2 class="text-lg font-semibold text-foreground">Sumber Data</h2>
        </template>
        <div class="flex items-center gap-4">
          <Database class="w-10 h-10 text-primary" />
          <div>
            <p class="text-3xl font-bold text-foreground">{{ dashboardStore.stats?.source_count ?? 0 }}</p>
            <p class="text-sm text-muted-foreground">sumber terdaftar</p>
          </div>
        </div>
        <router-link to="/app/sources" class="inline-block mt-4 text-sm text-primary hover:underline">
          Kelola sumber data &rarr;
        </router-link>
      </Card>

      <Card custom-class="lg:col-span-2">
        <template #header>
          <h2 class="text-lg font-semibold text-foreground">Aktivitas Terbaru</h2>
        </template>
        <ul v-if="dashboardStore.stats?.recent_activity?.length" class="space-y-3">
          <li v-for="(item, idx) in dashboardStore.stats.recent_activity" :key="idx"
            class="flex items-start justify-between gap-4 pb-3 border-b border-border last:border-0 last:pb-0">
            <div>
              <p class="text-sm text-foreground">{{ item.detail }}</p>
              <p class="text-xs text-muted-foreground mt-1">{{ item.entity_type }} &middot; {{ item.action }}</p>
            </div>
            <span class="text-xs text-muted-foreground whitespace-nowrap">{{ formatDate(item.created_at) }}</span>
          </li>
        </ul>
        <p v-else class="text-sm text-muted-foreground">Belum ada aktivitas.</p>
      </Card>
    </div>
  </div>
</template>
