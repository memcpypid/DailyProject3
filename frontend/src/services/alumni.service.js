import api from "./api";

class AlumniService {
  list(params = {}) {
    return api.get("/api/v1/alumni", { params });
  }

  get(id) {
    return api.get(`/api/v1/alumni/${id}`);
  }

  create(payload) {
    return api.post("/api/v1/alumni", payload);
  }

  update(id, payload) {
    return api.put(`/api/v1/alumni/${id}`, payload);
  }

  remove(id) {
    return api.delete(`/api/v1/alumni/${id}`);
  }

  candidates(id) {
    return api.get(`/api/v1/alumni/${id}/candidates`);
  }

  addManualCandidate(id, payload) {
    return api.post(`/api/v1/alumni/${id}/candidates/manual`, payload);
  }

  reviewCandidate(alumniId, candidateId, decision) {
    return api.post(`/api/v1/alumni/${alumniId}/candidates/${candidateId}/review`, { decision });
  }

  searchWeb(id) {
    return api.get(`/api/v1/alumni/${id}/search-web`);
  }

  importExcel(file, { dryRun = false, limit = null } = {}) {
    const formData = new FormData();
    formData.append("file", file);
    const params = { dry_run: dryRun };
    if (limit) params.limit = limit;
    return api.post("/api/v1/alumni/import", formData, {
      params,
      headers: { "Content-Type": "multipart/form-data" },
    });
  }
}

export default new AlumniService();
