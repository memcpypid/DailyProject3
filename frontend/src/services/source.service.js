import api from "./api";

class SourceService {
  list() {
    return api.get("/api/v1/sources");
  }

  create(payload) {
    return api.post("/api/v1/sources", payload);
  }

  update(id, payload) {
    return api.put(`/api/v1/sources/${id}`, payload);
  }

  remove(id) {
    return api.delete(`/api/v1/sources/${id}`);
  }
}

export default new SourceService();
