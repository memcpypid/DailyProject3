import { defineStore } from "pinia";
import { ref } from "vue";
import sourceService from "@/services/source.service";
import { useToast } from "@/composables/useToast";

export const useSourceStore = defineStore("sources", () => {
  const toast = useToast();

  const items = ref([]);
  const loading = ref(false);

  const fetchList = async () => {
    loading.value = true;
    try {
      const res = await sourceService.list();
      items.value = res.data.data;
    } catch (err) {
      toast.error(err.response?.data?.detail || "Gagal memuat sumber data");
    } finally {
      loading.value = false;
    }
  };

  const create = async (payload) => {
    const res = await sourceService.create(payload);
    toast.success("Sumber data berhasil ditambahkan");
    return res.data.data;
  };

  const update = async (id, payload) => {
    const res = await sourceService.update(id, payload);
    toast.success("Sumber data berhasil diperbarui");
    return res.data.data;
  };

  const remove = async (id) => {
    await sourceService.remove(id);
    toast.success("Sumber data berhasil dihapus");
  };

  return { items, loading, fetchList, create, update, remove };
});
