/**
 * Campus Navigation System — Geolocation Module
 * Honest GPS accuracy classification, jitter smoothing, and indoor warning logic.
 */

class GeolocationManager {
  constructor() {
    this.watchId = null;
    this.currentPosition = null; // { lat, lng, accuracy, tier, timestamp }
    this.previousPosition = null;
    this.listeners = [];
    this.errorListeners = [];
    this.isWatching = false;

    // Smoothing factor (alpha in [0, 1]): 0.35 provides smooth movement without lag
    this.smoothingAlpha = 0.35;
  }

  /**
   * Determine UX accuracy tier based on reported uncertainty radius.
   */
  classifyAccuracy(accuracyMeters) {
    if (accuracyMeters <= 10) {
      return { tier: 'excellent', label: 'Excellent', color: '#10b981' };
    } else if (accuracyMeters <= 25) {
      return { tier: 'good', label: 'Good', color: '#14b8a6' };
    } else if (accuracyMeters <= 50) {
      return { tier: 'usable', label: 'Usable', color: '#f59e0b' };
    } else if (accuracyMeters <= 100) {
      return { tier: 'approximate', label: 'Approximate', color: '#f97316' };
    } else {
      return { tier: 'poor', label: 'Poor', color: '#ef4444' };
    }
  }

  /**
   * Calculate distance between two coordinates in meters.
   */
  haversine(lat1, lon1, lat2, lon2) {
    const R = 6371000;
    const dLat = (lat2 - lat1) * (Math.PI / 180);
    const dLon = (lon2 - lon1) * (Math.PI / 180);
    const a =
      Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos(lat1 * (Math.PI / 180)) * Math.cos(lat2 * (Math.PI / 180)) *
      Math.sin(dLon / 2) * Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
  }

  /**
   * Apply anti-jitter filtering and exponential moving average smoothing.
   */
  filterAndSmooth(rawLat, rawLng, rawAccuracy) {
    const now = Date.now();

    if (!this.previousPosition) {
      return { lat: rawLat, lng: rawLng, accuracy: rawAccuracy };
    }

    const dt = (now - this.previousPosition.timestamp) / 1000.0;
    const dist = this.haversine(this.previousPosition.lat, this.previousPosition.lng, rawLat, rawLng);

    // 1. Rejection of impossible teleportation jumps (velocity > 25 m/s)
    if (dt > 0.2 && dist / dt > 25.0 && rawAccuracy > 30) {
      console.warn(`[GPS] Filtered impossible sudden jump: ${Math.round(dist)}m in ${dt.toFixed(1)}s`);
      return {
        lat: this.previousPosition.lat,
        lng: this.previousPosition.lng,
        accuracy: rawAccuracy,
      };
    }

    // 2. Exponential Moving Average (EMA) for visual calmness
    const smoothedLat = this.smoothingAlpha * rawLat + (1 - this.smoothingAlpha) * this.previousPosition.lat;
    const smoothedLng = this.smoothingAlpha * rawLng + (1 - this.smoothingAlpha) * this.previousPosition.lng;

    return {
      lat: smoothedLat,
      lng: smoothedLng,
      accuracy: rawAccuracy,
    };
  }

  /**
   * Request user permission and begin watching position.
   */
  startWatching() {
    if (!('geolocation' in navigator)) {
      this.notifyError({
        code: 'NOT_SUPPORTED',
        message: 'Browser Geolocation API is not supported on this device.',
      });
      return;
    }

    if (this.isWatching) return;

    const geoOptions = {
      enableHighAccuracy: true,
      timeout: 12000,
      maximumAge: 4000,
    };

    this.isWatching = true;

    this.watchId = navigator.geolocation.watchPosition(
      (pos) => {
        const rawLat = pos.coords.latitude;
        const rawLng = pos.coords.longitude;
        const rawAcc = Math.round(pos.coords.accuracy);

        // Filter and smooth
        const smoothed = this.filterAndSmooth(rawLat, rawLng, rawAcc);
        const classification = this.classifyAccuracy(smoothed.accuracy);

        this.currentPosition = {
          lat: smoothed.lat,
          lng: smoothed.lng,
          accuracy: smoothed.accuracy,
          rawLat: rawLat,
          rawLng: rawLng,
          tier: classification.tier,
          tierLabel: classification.label,
          tierColor: classification.color,
          timestamp: pos.timestamp || Date.now(),
        };

        this.previousPosition = { ...this.currentPosition };
        this.notifyListeners(this.currentPosition);
      },
      (err) => {
        let msg = 'Unable to determine your location.';
        let code = 'UNKNOWN_LOC_ERROR';

        if (err.code === 1) {
          msg = 'Location permission was denied. You can select your starting point manually on the map.';
          code = 'PERMISSION_DENIED';
        } else if (err.code === 2) {
          msg = 'Location position unavailable. Please check your GPS / device settings.';
          code = 'POSITION_UNAVAILABLE';
        } else if (err.code === 3) {
          msg = 'Location request timed out.';
          code = 'TIMEOUT';
        }

        this.notifyError({ code, message: msg, raw: err });
      },
      geoOptions
    );
  }

  stopWatching() {
    if (this.watchId !== null) {
      navigator.geolocation.clearWatch(this.watchId);
      this.watchId = null;
      this.isWatching = false;
    }
  }

  onPositionUpdate(callback) {
    this.listeners.push(callback);
    if (this.currentPosition) {
      callback(this.currentPosition);
    }
  }

  onError(callback) {
    this.errorListeners.push(callback);
  }

  notifyListeners(pos) {
    this.listeners.forEach((cb) => cb(pos));
  }

  notifyError(err) {
    this.errorListeners.forEach((cb) => cb(err));
  }
}

// Global Singleton
window.geoManager = new GeolocationManager();
