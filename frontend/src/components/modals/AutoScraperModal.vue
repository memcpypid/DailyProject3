<script setup>
import { ref, onMounted, onUnmounted, watch, computed } from 'vue';
import { 
  X, Play, Square, RefreshCw, Bot, Sparkles, CheckCircle2, 
  ExternalLink, Mail, Phone, Building2, Briefcase, Globe, 
  Linkedin, Instagram, Facebook, AlertCircle, Clock
} from 'lucide-vue-next';
import scraperService from '@/services/scraper.service';
import { useToast } from '@/composables/useToast';
import Button from '@/components/ui/Button.vue';
import Input from '@/components/ui/Input.vue';
import Select from '@/components/ui/Select.vue';
import Badge from '@/components/ui/Badge.vue';

const props = defineProps({
  isOpen: { type: Boolean, required: true },
});

const emit = defineEmits(['close', 'updated']);
const toast = useToast();

const workers = ref(10);
const limit = ref(50);
const statusFilter = ref('BELUM_DILACAK');
const univKeyword = ref('');
const delayMin = ref(0.8);
const delayMax = ref(2.0);

const status = ref({
  is_running: false,
  stop_requested: false,
  workers: 10,
  total_queued: 0,
  processed_count: 0,
  found_count: 0,
  progress_percent: 0,
  elapsed_seconds: 0,
  current_name: '',
});

const logs = ref([]);
const starting = ref(false);
const stopping = ref(false);
let pollTimer = null;

const statusOptions = [
  { value: 'BELUM_DILACAK', label: 'Hanya Status: Belum Dilacak' },
  { value: 'ALL', label: 'Semua Status (Re-Scrape Seluruh Alumni)' },
];

const fetchStatusAndLogs = async () => {
  try {
    const [statusRes, logsRes] = await Promise.all([
      scraperService.getStatus(),
      scraperService.getLogs(60),
    ]);
    status.value = statusRes.data.data;
    logs.value = logsRes.data.data || [];

    if (status.value.is_running) {
      emit('updated');
    }
  } catch (err) {
    // Silent polling error
  }
};

const startPolling = () => {
  stopPolling();
  fetchStatusAndLogs();
  pollTimer = setInterval(fetchStatusAndLogs, 2000);
};

const stopPolling = () => {
  if (pollTimer) {
    clearInterval(pollTimer);
    pollTimer = null;
  }
};

watch(
  () => props.isOpen,
  (open) => {
    if (open) {
      startPolling();
    } else {
      stopPolling();
    }
  }
);

onMounted(() => {
  if (props.isOpen) startPolling();
});

onUnmounted(() => {
  stopPolling();
});

const startScraping = async () => {
  starting.value = true;
  try {
    await scraperService.start({
      workers: Number(workers.value),
      limit: Number(limit.value),
      status_filter: statusFilter.value,
      univ_keyword: univKeyword.value,
      delay_min: Number(delayMin.value),
      delay_max: Number(delayMax.value),
    });
    toast.success(`Scraping OSINT dimulai dengan ${workers.value} worker paralel!`);
    await fetchStatusAndLogs();
    emit('updated');
  } catch (err) {
    toast.error(err.response?.data?.detail || 'Gagal memulai scraping');
  } finally {
    starting.value = false;
  }
};

const stopScraping = async () => {
  stopping.value = true;
  try {
    await scraperService.stop();
    toast.info('Perintah penghentian dikirim');
    await fetchStatusAndLogs();
    emit('updated');
  } catch (err) {
    toast.error(err.response?.data?.detail || 'Gagal menghentikan scraper');
  } finally {
    stopping.value = false;
  }
};

const formatTime = (secs) => {
  const m = Math.floor(secs / 60);
  const s = secs % 60;
  return `${m}m ${s < 10 ? '0' : ''}${s}s`;
};

const resultLogs = computed(() => {
  return logs.value.slice().reverse();
});
</script>

<template>
  <div v-if="isOpen" class="fixed inset-0 z-50 overflow-y-auto" role="dialog" aria-modal="true">
    <div class="fixed inset-0 bg-black/40 backdrop-blur-sm" @click="emit('close')"></div>

    <div class="flex min-h-screen items-center justify-center p-3 sm:p-4 text-center">
      <div class="relative w-full max-w-4xl overflow-hidden rounded-xl bg-card text-left shadow-2xl border border-border flex flex-col max-h-[90vh]" @click.stop>
        
        <!-- Header -->
        <div class="flex items-center justify-between border-b border-border px-6 py-4 bg-muted/30">
          <div class="flex items-center gap-3">
            <div class="relative flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10 text-primary border border-primary/20">
              <Bot class="h-5 w-5" />
              <span v-if="status.is_running" class="absolute -top-1 -right-1 flex h-3 w-3">
                <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span class="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
              </span>
            </div>
            <div>
              <div class="flex items-center gap-2">
                <h3 class="text-lg font-bold text-foreground">Auto-Scraping & OSINT Bot</h3>
                <Badge :variant="status.is_running ? 'success' : 'secondary'">
                  {{ status.is_running ? `Aktif (${status.workers} Worker)` : 'Standby / Siap' }}
                </Badge>
              </div>
              <p class="text-xs text-muted-foreground mt-0.5">
                Pencarian otomatis data alumni secara paralel (Medsos, Email, No HP, Pekerjaan, Sektor) langsung ke database.
              </p>
            </div>
          </div>
          <button @click="emit('close')" class="rounded-lg p-1.5 text-muted-foreground hover:bg-accent hover:text-foreground">
            <X class="w-5 h-5" />
          </button>
        </div>

        <!-- Body Area -->
        <div class="p-6 overflow-y-auto space-y-6 flex-1">
          
          <!-- Control Panel (Saat Tidak Running) -->
          <div v-if="!status.is_running" class="grid grid-cols-1 sm:grid-cols-3 gap-4 p-4 rounded-xl bg-secondary/30 border border-border">
            <div>
              <label class="block text-xs font-semibold text-foreground mb-1.5">Jumlah Worker Paralel</label>
              <Input type="number" v-model="workers" :min="1" :max="20" placeholder="10" />
              <span class="text-[11px] text-muted-foreground">Rekomendasi: 5 - 10 worker</span>
            </div>
            <div>
              <label class="block text-xs font-semibold text-foreground mb-1.5">Batas Jumlah Alumni (Limit)</label>
              <Input type="number" v-model="limit" :min="0" placeholder="50" />
              <span class="text-[11px] text-muted-foreground">Isi 0 untuk proses seluruh alumni</span>
            </div>
            <div>
              <label class="block text-xs font-semibold text-foreground mb-1.5">Target Status Alumni</label>
              <Select v-model="statusFilter" :options="statusOptions" />
              <span class="text-[11px] text-muted-foreground">Target data yang ingin dicari</span>
            </div>
          </div>

          <!-- Live Running Stats (Saat Running) -->
          <div v-if="status.is_running || status.processed_count > 0" class="space-y-4">
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div class="p-3.5 rounded-xl border border-border bg-card">
                <span class="text-xs text-muted-foreground block">Progress Scraping</span>
                <span class="text-lg font-bold text-foreground">{{ status.processed_count }} / {{ status.total_queued }}</span>
                <span class="text-xs text-primary font-medium block">({{ status.progress_percent }}%)</span>
              </div>
              <div class="p-3.5 rounded-xl border border-border bg-card">
                <span class="text-xs text-muted-foreground block">Profil Ditemukan</span>
                <span class="text-lg font-bold text-emerald-500">{{ status.found_count }}</span>
                <span class="text-xs text-muted-foreground block">Data Berhasil Diperkaya</span>
              </div>
              <div class="p-3.5 rounded-xl border border-border bg-card">
                <span class="text-xs text-muted-foreground block">Durasi Waktu</span>
                <span class="text-lg font-bold text-foreground">{{ formatTime(status.elapsed_seconds) }}</span>
                <span class="text-xs text-muted-foreground block">{{ status.workers }} Worker Paralel</span>
              </div>
              <div class="p-3.5 rounded-xl border border-border bg-card">
                <span class="text-xs text-muted-foreground block">Sedang Memproses</span>
                <span class="text-sm font-semibold text-foreground truncate block" :title="status.current_name">
                  {{ status.current_name || '-' }}
                </span>
                <span class="text-xs text-amber-500 font-medium block">Pencarian Live</span>
              </div>
            </div>

            <!-- Progress Bar -->
            <div class="w-full bg-secondary rounded-full h-2.5 overflow-hidden">
              <div 
                class="bg-primary h-2.5 rounded-full transition-all duration-300 ease-out" 
                :style="{ width: `${Math.min(100, Math.max(0, status.progress_percent))}%` }">
              </div>
            </div>
          </div>

          <!-- Live Feed Log Hasil Temuan -->
          <div>
            <div class="flex items-center justify-between mb-3">
              <h4 class="text-sm font-semibold text-foreground flex items-center gap-2">
                <Sparkles class="w-4 h-4 text-amber-500" />
                Live Log Hasil Temuan Data OSINT (Real-Time)
              </h4>
              <span class="text-xs text-muted-foreground">{{ resultLogs.length }} aktivitas tercatat</span>
            </div>

            <div class="border border-border rounded-xl bg-secondary/15 h-72 overflow-y-auto p-3 space-y-2 font-mono text-xs">
              <div v-if="!resultLogs.length" class="h-full flex flex-col items-center justify-center text-muted-foreground gap-2">
                <Bot class="w-8 h-8 opacity-40" />
                <span>Belum ada aktivitas. Tekan "Mulai Pencarian Data Otomatis" untuk menjalankan.</span>
              </div>

              <div 
                v-for="(log, idx) in resultLogs" 
                :key="idx" 
                class="p-3 rounded-lg border transition-all text-xs"
                :class="log.type === 'system' ? 'bg-primary/5 border-primary/20 text-primary' : (log.has_found ? 'bg-emerald-500/10 border-emerald-500/30 text-foreground' : 'bg-background/80 border-border text-muted-foreground')">
                
                <!-- System message -->
                <div v-if="log.type === 'system'" class="flex items-center gap-2 font-sans font-medium">
                  <Clock class="w-3.5 h-3.5 shrink-0" />
                  <span>[{{ log.timestamp }}]</span>
                  <span>{{ log.message }}</span>
                </div>

                <!-- Scraping result item -->
                <div v-else class="space-y-1.5 font-sans">
                  <div class="flex items-center justify-between">
                    <div class="flex items-center gap-2">
                      <span class="font-semibold text-foreground">{{ log.name }}</span>
                      <span class="text-muted-foreground">({{ log.nim || 'Tanpa NIM' }})</span>
                      <span v-if="log.prodi" class="text-muted-foreground">&middot; {{ log.prodi }}</span>
                    </div>
                    <span 
                      class="px-2 py-0.5 text-[10px] font-semibold rounded-full"
                      :class="log.has_found ? 'bg-emerald-500/20 text-emerald-600 dark:text-emerald-400' : 'bg-secondary text-muted-foreground'">
                      {{ log.has_found ? '✅ DATA DITEMUKAN' : '❌ BELUM DITEMUKAN' }}
                    </span>
                  </div>

                  <!-- Details when found -->
                  <div v-if="log.has_found" class="grid grid-cols-1 sm:grid-cols-2 gap-x-4 gap-y-1 text-xs pt-1 border-t border-border/50 text-muted-foreground">
                    <div v-if="log.linkedin" class="flex items-center gap-1.5 truncate">
                      <Linkedin class="w-3.5 h-3.5 text-blue-500 shrink-0" />
                      <a :href="log.linkedin" target="_blank" class="text-primary hover:underline truncate">{{ log.linkedin }}</a>
                    </div>
                    <div v-if="log.instagram" class="flex items-center gap-1.5 truncate">
                      <Instagram class="w-3.5 h-3.5 text-pink-500 shrink-0" />
                      <a :href="log.instagram" target="_blank" class="text-primary hover:underline truncate">{{ log.instagram }}</a>
                    </div>
                    <div v-if="log.email" class="flex items-center gap-1.5 truncate">
                      <Mail class="w-3.5 h-3.5 text-amber-500 shrink-0" />
                      <span class="text-foreground truncate">{{ log.email }}</span>
                    </div>
                    <div v-if="log.phone" class="flex items-center gap-1.5 truncate">
                      <Phone class="w-3.5 h-3.5 text-emerald-500 shrink-0" />
                      <span class="text-foreground">{{ log.phone }}</span>
                    </div>
                    <div v-if="log.employer || log.position" class="flex items-center gap-1.5 sm:col-span-2 truncate">
                      <Briefcase class="w-3.5 h-3.5 text-purple-500 shrink-0" />
                      <span class="text-foreground truncate">
                        <b>{{ log.position || 'Bekerja' }}</b> @ {{ log.employer || '-' }}
                        <span v-if="log.sector" class="text-xs text-primary font-medium">({{ log.sector }})</span>
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Footer Actions -->
        <div class="border-t border-border px-6 py-4 bg-muted/20 flex flex-col sm:flex-row items-center justify-between gap-3">
          <div class="text-xs text-muted-foreground">
            <span v-if="status.is_running" class="flex items-center gap-1.5 text-emerald-600 dark:text-emerald-400 font-medium">
              <span class="relative flex h-2 w-2">
                <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span class="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
              </span>
              Scraper sedang berjalan di latar belakang...
            </span>
            <span v-else>Tekan mulai untuk melakukan scraping data otomatis.</span>
          </div>

          <div class="flex items-center gap-2 w-full sm:w-auto justify-end">
            <Button variant="outline" @click="emit('close')">
              Tutup
            </Button>
            
            <Button 
              v-if="status.is_running" 
              variant="destructive" 
              :loading="stopping" 
              @click="stopScraping">
              <template #icon-left><Square class="w-4 h-4 mr-2" /></template>
              Hentikan Scraping
            </Button>

            <Button 
              v-else 
              variant="primary" 
              :loading="starting" 
              @click="startScraping"
              class="bg-emerald-600 hover:bg-emerald-700 text-white">
              <template #icon-left><Play class="w-4 h-4 mr-2" /></template>
              Mulai Scraping Otomatis
            </Button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
