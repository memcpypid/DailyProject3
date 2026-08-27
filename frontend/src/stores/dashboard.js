import { defineStore } from "pinia";
import { ref } from "vue";
import dashboardService from "@/services/dashboard.service";
import { useToast } from "@/composables/useToast";

export const useDashboardStore = defineStore("dashboard", () => {
  const toast = useToast();

  const stats = ref(null);
  const loading = ref(false);

  const fetchStats = async () => {
    loading.value = true;
    try {
      const res = await dashboardService.stats();
      stats.value = res.data.data;
    } catch (err) {
      toast.error(err.response?.data?.detail || "Gagal memuat statistik");
    } finally {
      loading.value = false;
    }
  };

  return { stats, loading, fetchStats };
});
