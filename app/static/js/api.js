/**
 * Campus Navigation System — API Client
 * Centralized Fetch wrapper with error normalization and JSON parsing.
 */

const Api = {
  baseUrl: '/api/v1',

  async request(endpoint, options = {}) {
    const config = {
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, config);
      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        const errorMsg = data?.error?.message || `HTTP error! status: ${response.status}`;
        const error = new Error(errorMsg);
        error.code = data?.error?.code || 'UNKNOWN_ERROR';
        error.status = response.status;
        throw error;
      }

      return data;
    } catch (err) {
      console.error(`API Error on ${endpoint}:`, err);
      throw err;
    }
  },

  async getCampuses() {
    const res = await this.request('/campuses');
    return res.data;
  },

  async getCampusMapData(campusId) {
    const res = await this.request(`/campuses/${campusId}/map-data`);
    return res.data;
  },

  async searchLocations(query, campusId, category = '') {
    const params = new URLSearchParams({
      q: query,
      campus_id: campusId,
    });
    if (category) {
      params.append('category', category);
    }
    const res = await this.request(`/search?${params.toString()}`);
    return res.data;
  },

  async calculateRoute(campusId, origin, destination, accessible = false) {
    const payload = {
      campus_id: campusId,
      origin: origin,
      destination: destination,
      accessible: accessible,
    };
    const res = await this.request('/routes', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    return res.data.route;
  },
};
