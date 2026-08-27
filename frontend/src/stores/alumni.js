import { defineStore } from "pinia";
import { ref } from "vue";
import alumniService from "@/services/alumni.service";
import { useToast } from "@/composables/useToast";

export const useAlumniStore = defineStore("alumni", () => {
  const toast = useToast();

  const items = ref([]);
  const pagination = ref({ page: 1, limit: 10, total: 0, total_pages: 1, has_next: false, has_previous: false });
  const current = ref(null);
  const candidates = ref([]);
  const loading = ref(false);
  const importing = ref(false);
  const searching = ref(false);
  const searchResults = ref([]);

  const fetchList = async (params = {}) => {
    loading.value = true;
    try {
      const res = await alumniService.list(params);
      items.value = res.data.data.alumni;
      pagination.value = res.data.data.pagination;
    } catch (err) {
      toast.error(err.response?.data?.detail || "Gagal memuat daftar alumni");
    } finally {
      loading.value = false;
    }
  };

  const fetchOne = async (id) => {
    loading.value = true;
    try {
      const res = await alumniService.get(id);
      current.value = res.data.data;
    } catch (err) {
      toast.error(err.response?.data?.detail || "Gagal memuat data alumni");
    } finally {
      loading.value = false;
    }
  };

  const fetchCandidates = async (id) => {
    try {
      const res = await alumniService.candidates(id);
      candidates.value = res.data.data;
    } catch (err) {
      toast.error(err.response?.data?.detail || "Gagal memuat kandidat");
    }
  };

  const create = async (payload) => {
    const res = await alumniService.create(payload);
    toast.success("Alumni berhasil ditambahkan");
    return res.data.data;
  };

  const update = async (id, payload) => {
    const res = await alumniService.update(id, payload);
    toast.success("Alumni berhasil diperbarui");
    return res.data.data;
  };

  const remove = async (id) => {
    await alumniService.remove(id);
    toast.success("Alumni berhasil dihapus");
  };

  const addManualCandidate = async (id, payload) => {
    const res = await alumniService.addManualCandidate(id, payload);
    toast.success("Temuan manual tersimpan");
    return res.data.data;
  };

  const searchWeb = async (id) => {
    searching.value = true;
    searchResults.value = [];
    try {
      const res = await alumniService.searchWeb(id);
      searchResults.value = res.data.data;
      return res.data.data;
    } catch (err) {
      toast.error(err.response?.data?.detail || "Pencarian web gagal");
      throw err;
    } finally {
      searching.value = false;
    }
  };

  const importExcel = async (file, options = {}) => {
    importing.value = true;
    try {
      const res = await alumniService.importExcel(file, options);
      const summary = res.data.data;
      if (!options.dryRun) {
        toast.success(
          `Impor selesai: ${summary.created} baru, ${summary.skipped_duplicate} duplikat dilewati` +
            (summary.skipped_invalid ? `, ${summary.skipped_invalid} baris tidak valid` : "")
        );
      }
      return summary;
    } catch (err) {
      toast.error(err.response?.data?.detail || "Impor gagal");
      throw err;
    } finally {
      importing.value = false;
    }
  };

  return {
    items,
    pagination,
    current,
    candidates,
    loading,
    importing,
    searching,
    searchResults,
    fetchList,
    fetchOne,
    fetchCandidates,
    create,
    update,
    remove,
    addManualCandidate,
    importExcel,
    searchWeb,
  };
});
