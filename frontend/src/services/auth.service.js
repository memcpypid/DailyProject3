import api from "./api";

/**
 * @typedef {Object} UserResponse
 * @property {string} id
 * @property {string} name
 * @property {string} email
 * @property {string} role
 * @property {boolean} is_verified
 * @property {string} created_at
 * @property {string} updated_at
 */

/**
 * @typedef {Object} LoginRequest
 * @property {string} email
 * @property {string} password
 */

class AuthService {
  /**
   * Endpoint for user login
   * @param {LoginRequest} credentials - Contains email and password
   * @returns {Promise<import('axios').AxiosResponse<{success: boolean, message: string, data: {access_token: string, refresh_token: string, user: UserResponse}}>>}
   */
  login(credentials) {
    return api.post("/api/v1/auth/login", credentials);
  }

  /**
   * Endpoint for user logout
   * @param {string} refreshToken - The refresh token to be invalidated
   * @returns {Promise<import('axios').AxiosResponse<{success: boolean, message: string}>>}
   */
  logout(refreshToken) {
    return api.post("/api/v1/auth/logout", { refresh_token: refreshToken });
  }

  /**
   * Endpoint for user registration
   * @param {Object} payload - Registration info (name, email, password)
   * @returns {Promise<import('axios').AxiosResponse<{success: boolean, message: string}>>}
   */
  register(payload) {
    return api.post("/api/v1/auth/register", payload);
  }

  /**
   * Endpoint to update current user profile
   * @param {Object} payload - Update payload (name, password)
   * @returns {Promise<import('axios').AxiosResponse<{success: boolean, message: string, data: UserResponse}>>}
   */
  updateProfile(payload) {
    return api.put("/api/v1/users/me", payload);
  }

  /**
   * Endpoint to fetch current user profile
   * @returns {Promise<import('axios').AxiosResponse<{success: boolean, message: string, data: UserResponse}>>}
   */
  fetchProfile() {
    return api.get("/api/v1/users/me");
  }
}

export default new AuthService();
