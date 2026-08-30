import api from "./api";

class ScraperService {
  start(payload = {}) {
    return api.post("/api/v1/scraper/start", payload);
  }

  stop() {
    return api.post("/api/v1/scraper/stop");
  }

  getStatus() {
    return api.get("/api/v1/scraper/status");
  }

  getLogs(limit = 50) {
    return api.get("/api/v1/scraper/logs", { params: { limit } });
  }
}

export default new ScraperService();
