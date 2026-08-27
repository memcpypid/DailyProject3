<script setup>
import { onMounted, ref, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ArrowLeft, ExternalLink, Info, PenLine, Linkedin, Instagram, Facebook, Music2, Mail, Phone, Building2, BadgeCheck, Search } from 'lucide-vue-next';
import { useAlumniStore } from '@/stores/alumni';
import { useSourceStore } from '@/stores/sources';
import { parseContactInfo } from '@/utils/parseContactInfo';
import { useStatusBadge } from '@/composables/useStatusBadge';
import Card from '@/components/ui/Card.vue';
import Button from '@/components/ui/Button.vue';
import Badge from '@/components/ui/Badge.vue';
import Skeleton from '@/components/ui/Skeleton.vue';
import ManualCandidateModal from '@/components/modals/ManualCandidateModal.vue';

const route = useRoute();
const router = useRouter();
const alumniStore = useAlumniStore();
const sourceStore = useSourceStore();
const { statusInfo } = useStatusBadge();

const alumniId = computed(() => route.params.id);
const manualModalOpen = ref(false);
const manualInitialData = ref(null);
const searchPanelOpen = ref(false);

const load = async () => {
  await alumniStore.fetchOne(alumniId.value);
  await alumniStore.fetchCandidates(alumniId.value);
  if (!sourceStore.items.length) await sourceStore.fetchList();
};

onMounted(load);

const openManualModal = (initialData = null) => {
  manualInitialData.value = initialData;
  manualModalOpen.value = true;
};

const sourceNameForLink = (link) => {
  if (link.includes('linkedin.com')) return 'LinkedIn';
  if (link.includes('instagram.com')) return 'Instagram';
  if (link.includes('facebook.com')) return 'Facebook';
  if (link.includes('tiktok.com')) return 'TikTok';
  return 'Mesin Pencari Umum';
};

const runSearchWeb = async () => {
  searchPanelOpen.value = true;
  await alumniStore.searchWeb(alumniId.value);
};

const useSearchResult = (result) => {
  // source_id: pakai sumber yang benar-benar memicu query ini (kalau ada) - lebih akurat
  // daripada menebak dari domain link, karena mencerminkan konfigurasi sumber sungguhan.
  const sourceForId = result.queried_source || sourceNameForLink(result.link);
  const source = sourceStore.items.find((s) => s.name === sourceForId) || sourceStore.items.find((s) => s.name === 'Mesin Pencari Umum');
  // Isi otomatis kolom URL sosial media: selalu berdasar domain link itu sendiri,
  // terlepas dari query mana yang menemukannya.
  const platform = sourceNameForLink(result.link);
  const initialData = {
    source_id: source?.id || '',
    raw_name: alumniStore.current.full_name,
    snippet: `[${result.target_data}] ${result.title} - ${result.snippet} (${result.link})`,
  };
  if (platform === 'LinkedIn') initialData.linkedin_url = result.link;
  if (platform === 'Instagram') initialData.instagram_url = result.link;
  if (platform === 'Facebook') initialData.facebook_url = result.link;
  if (platform === 'TikTok') initialData.tiktok_url = result.link;

  // Tarik nomor HP/email/medsos lain yang disebut di judul & cuplikan hasil pencarian.
  const parsed = parseContactInfo(`${result.title} ${result.snippet}`);
  for (const [key, value] of Object.entries(parsed)) {
    if (!initialData[key]) initialData[key] = value;
  }

  searchPanelOpen.value = false;
  openManualModal(initialData);
};

const socialLinks = (candidate) => [
  { icon: Linkedin, url: candidate.linkedin_url, label: 'LinkedIn' },
  { icon: Instagram, url: candidate.instagram_url, label: 'Instagram' },
  { icon: Facebook, url: candidate.facebook_url, label: 'Facebook' },
  { icon: Music2, url: candidate.tiktok_url, label: 'TikTok' },
].filter((l) => l.url);

const formatDate = (iso) => (iso ? new Date(iso).toLocaleString('id-ID', { dateStyle: 'medium', timeStyle: 'short' }) : '-');
</script>

<template>
  <div class="space-y-6">
    <button @click="router.push('/app/alumni')" class="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground">
      <ArrowLeft class="w-4 h-4" /> Kembali ke Data Alumni
    </button>

    <Skeleton v-if="alumniStore.loading && !alumniStore.current" height="10rem" />

    <template v-else-if="alumniStore.current">
      <Card>
        <div class="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
          <div>
            <div class="flex items-center gap-3">
              <h1 class="text-2xl font-bold text-foreground">{{ alumniStore.current.full_name }}</h1>
              <Badge :variant="statusInfo(alumniStore.current.status).variant">
                {{ statusInfo(alumniStore.current.status).label }}
              </Badge>
            </div>
            <p class="text-sm text-muted-foreground mt-1">
              NIM {{ alumniStore.current.nim || '-' }} &middot; {{ alumniStore.current.fakultas || '-' }} -
              {{ alumniStore.current.program_studi || '-' }}
            </p>
            <p class="text-sm text-muted-foreground mt-1">
              Masuk {{ alumniStore.current.tahun_masuk || '-' }} &middot; Lulus {{ alumniStore.current.tanggal_lulus || '-' }}
            </p>
            <p v-if="alumniStore.current.name_variations?.length" class="text-xs text-muted-foreground mt-2">
              Variasi nama: {{ alumniStore.current.name_variations.join(', ') }}
            </p>
          </div>
          <div class="text-right shrink-0">
            <p class="text-xs text-muted-foreground">Terakhir diverifikasi: {{ formatDate(alumniStore.current.last_verified_at) }}</p>
            <div class="flex gap-2 mt-3 justify-end">
              <Button variant="outline" @click="openManualModal()">
                <template #icon-left><PenLine class="w-4 h-4 mr-2" /></template>
                Input Manual
              </Button>
              <Button variant="outline" :loading="alumniStore.searching" @click="runSearchWeb">
                <template #icon-left><Search class="w-4 h-4 mr-2" /></template>
                Cari di Internet
              </Button>
            </div>
          </div>
        </div>
      </Card>

      <Card v-if="alumniStore.current.confirmed_profile" custom-class="border-primary/40 bg-primary/5">
        <div class="flex items-center gap-2 mb-3">
          <BadgeCheck class="w-5 h-5 text-primary" />
          <h2 class="text-base font-semibold text-foreground">Data Identitas Terkonfirmasi</h2>
          <Badge variant="success">Tersimpan di profil</Badge>
        </div>
        <div class="flex items-start gap-2 text-sm text-foreground">
          <Building2 class="w-4 h-4 mt-0.5 shrink-0 text-muted-foreground" />
          <div>
            <p>
              {{ alumniStore.current.confirmed_profile.position || '-' }}
              <span v-if="alumniStore.current.confirmed_profile.employment_type"> &middot; {{ alumniStore.current.confirmed_profile.employment_type }}</span>
            </p>
            <p class="text-muted-foreground">{{ alumniStore.current.confirmed_profile.employer_name || '-' }}</p>
            <p v-if="alumniStore.current.confirmed_profile.employer_address" class="text-xs text-muted-foreground">
              {{ alumniStore.current.confirmed_profile.employer_address }}
            </p>
          </div>
        </div>
        <div class="mt-2 space-y-1 text-xs text-muted-foreground">
          <p v-if="alumniStore.current.confirmed_profile.email" class="flex items-center gap-1.5">
            <Mail class="w-3.5 h-3.5" /> {{ alumniStore.current.confirmed_profile.email }}
          </p>
          <p v-if="alumniStore.current.confirmed_profile.phone" class="flex items-center gap-1.5">
            <Phone class="w-3.5 h-3.5" /> {{ alumniStore.current.confirmed_profile.phone }}
          </p>
        </div>
        <div v-if="socialLinks(alumniStore.current.confirmed_profile).length" class="flex gap-2 mt-3">
          <a v-for="link in socialLinks(alumniStore.current.confirmed_profile)" :key="link.label" :href="link.url" target="_blank" rel="noopener"
            :title="link.label" class="p-1.5 rounded-md bg-secondary text-secondary-foreground hover:bg-secondary/80">
            <component :is="link.icon" class="w-3.5 h-3.5" />
          </a>
        </div>
        <p class="text-xs text-muted-foreground mt-3">
          Sumber: {{ alumniStore.current.confirmed_profile.source_name }} &middot; diinput manual
        </p>
      </Card>

      <div>
        <h2 class="text-lg font-semibold text-foreground mb-3">Temuan Data Alumni</h2>

        <div v-if="!alumniStore.candidates.length" class="text-sm text-muted-foreground bg-card border border-border rounded-xl p-6">
          Belum ada temuan. Klik "Input Manual" untuk mencatat hasil riset Anda, atau "Cari di Internet" untuk mencari referensinya terlebih dahulu.
        </div>

        <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card v-for="candidate in alumniStore.candidates" :key="candidate.id"
            :custom-class="candidate.id === alumniStore.current.confirmed_candidate_id ? 'border-primary/40 ring-1 ring-primary/30' : ''">
            <div class="flex items-start justify-between mb-3">
              <div>
                <p class="font-semibold text-foreground">{{ candidate.raw_name || '(nama tidak tercatat)' }}</p>
                <p class="text-xs text-muted-foreground">{{ candidate.source_name }}</p>
              </div>
              <div class="text-right">
                <Badge v-if="candidate.id === alumniStore.current.confirmed_candidate_id" variant="success" custom-class="mt-1">
                  Terkonfirmasi
                </Badge>
                <Badge v-else variant="outline" custom-class="mt-1">Riwayat</Badge>
              </div>
            </div>

            <div class="flex items-start gap-2 text-sm text-foreground">
              <Building2 class="w-4 h-4 mt-0.5 shrink-0 text-muted-foreground" />
              <div>
                <p>{{ candidate.position || '-' }}<span v-if="candidate.employment_type"> &middot; {{ candidate.employment_type }}</span></p>
                <p class="text-muted-foreground">{{ candidate.employer_name || '-' }}</p>
                <p v-if="candidate.employer_address" class="text-xs text-muted-foreground">{{ candidate.employer_address }}</p>
              </div>
            </div>

            <div class="mt-2 space-y-1 text-xs text-muted-foreground">
              <p v-if="candidate.email" class="flex items-center gap-1.5"><Mail class="w-3.5 h-3.5" /> {{ candidate.email }}</p>
              <p v-if="candidate.phone" class="flex items-center gap-1.5"><Phone class="w-3.5 h-3.5" /> {{ candidate.phone }}</p>
            </div>

            <div v-if="socialLinks(candidate).length" class="flex gap-2 mt-3">
              <a v-for="link in socialLinks(candidate)" :key="link.label" :href="link.url" target="_blank" rel="noopener"
                :title="link.label" class="p-1.5 rounded-md bg-secondary text-secondary-foreground hover:bg-secondary/80">
                <component :is="link.icon" class="w-3.5 h-3.5" />
              </a>
              <a v-if="candidate.employer_social_media" :href="candidate.employer_social_media" target="_blank" rel="noopener"
                title="Sosial media tempat bekerja" class="p-1.5 rounded-md bg-secondary text-secondary-foreground hover:bg-secondary/80">
                <ExternalLink class="w-3.5 h-3.5" />
              </a>
            </div>

            <p v-if="candidate.snippet" class="text-xs text-muted-foreground mt-3 italic">{{ candidate.snippet }}</p>
          </Card>
        </div>

        <div class="flex items-start gap-2 mt-4 text-xs text-muted-foreground bg-secondary/50 border border-border rounded-lg p-3">
          <Info class="w-4 h-4 shrink-0 mt-0.5" />
          <p>
            Sistem ini tidak melakukan pengumpulan data pribadi otomatis-massal. Setiap temuan berasal dari riset
            manual satu-per-satu - gunakan "Cari di Internet" untuk mencari referensi, lalu simpan lewat "Input Manual"
            setelah Anda memverifikasi sendiri kecocokannya.
          </p>
        </div>
      </div>
    </template>

    <div v-if="searchPanelOpen" class="fixed inset-0 z-50 overflow-y-auto" role="dialog" aria-modal="true">
      <div class="fixed inset-0 bg-black/10 backdrop-blur-sm" @click="searchPanelOpen = false"></div>
      <div class="flex min-h-screen items-end justify-center p-4 text-center sm:items-center sm:p-0">
        <div class="relative overflow-hidden rounded-lg bg-card text-left shadow-xl sm:my-8 sm:w-full sm:max-w-xl border border-border" @click.stop>
          <div class="px-4 pb-4 pt-5 sm:p-6 max-h-[80vh] overflow-y-auto">
            <div class="flex justify-between items-center mb-2">
              <h3 class="text-lg font-semibold text-foreground">Hasil Pencarian Web</h3>
              <button @click="searchPanelOpen = false" class="text-muted-foreground hover:text-foreground">&times;</button>
            </div>
            <p class="text-xs text-muted-foreground mb-4">
              Pencarian untuk "{{ alumniStore.current?.full_name }}". Periksa tiap hasil dan pastikan itu benar-benar
              orang yang sama sebelum memilih "Gunakan hasil ini" - tidak ada yang tersimpan otomatis.
            </p>

            <div v-if="alumniStore.searching" class="text-sm text-muted-foreground py-6 text-center">Mencari...</div>
            <div v-else-if="!alumniStore.searchResults.length" class="text-sm text-muted-foreground py-6 text-center">
              Tidak ada hasil.
            </div>
            <div v-else class="space-y-3">
              <div v-for="result in alumniStore.searchResults" :key="result.link"
                class="border border-border rounded-lg p-3">
                <div class="flex items-center justify-between gap-2">
                  <a :href="result.link" target="_blank" rel="noopener" class="font-medium text-sm text-primary hover:underline">
                    {{ result.title }}
                  </a>
                  <Badge v-if="result.queried_source" variant="outline" custom-class="shrink-0">{{ result.queried_source }}</Badge>
                </div>
                <p v-if="result.target_data" class="text-xs font-medium text-primary mt-1">
                  Target data: {{ result.target_data }}
                </p>
                <p class="text-xs text-muted-foreground mt-1">{{ result.link }}</p>
                <p class="text-sm text-foreground mt-1.5">{{ result.snippet }}</p>
                <Button variant="outline" customClass="mt-2" @click="useSearchResult(result)">Gunakan hasil ini</Button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <ManualCandidateModal :is-open="manualModalOpen" :alumni-id="alumniId" :initial-data="manualInitialData"
      @close="manualModalOpen = false" @success="load" />
  </div>
</template>
