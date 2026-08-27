import api from "./api";

class DashboardService {
  stats() {
    return api.get("/api/v1/dashboard/stats");
  }
}

export default new DashboardService();
