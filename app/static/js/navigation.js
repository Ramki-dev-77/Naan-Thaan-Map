/**
 * Campus Navigation System — Navigation Controller
 * Manages active route calculation, step guidance, accessibility toggles, and recalculation.
 */

class NavigationController {
  constructor(options) {
    this.map = options.map;
    this.getCampusId = options.getCampusId;

    // DOM Elements
    this.destCard = document.getElementById('destinationCard');
    this.destBadge = document.getElementById('destBadge');
    this.destTitle = document.getElementById('destTitle');
    this.destSubtitle = document.getElementById('destSubtitle');
    this.destDescription = document.getElementById('destDescription');
    this.destMetaChips = document.getElementById('destMetaChips');
    this.startRouteBtn = document.getElementById('startRouteBtn');
    this.closeDestCard = document.getElementById('closeDestCard');

    this.navPanel = document.getElementById('navigationPanel');
    this.navOriginText = document.getElementById('navOriginText');
    this.navDestinationText = document.getElementById('navDestinationText');
    this.routeDistanceDisplay = document.getElementById('routeDistanceDisplay');
    this.routeTimeDisplay = document.getElementById('routeTimeDisplay');
    this.accessibleToggle = document.getElementById('accessibleToggle');
    this.navStepsList = document.getElementById('navStepsList');
    this.recalculateRouteBtn = document.getElementById('recalculateRouteBtn');
    this.clearRouteBtn = document.getElementById('clearRouteBtn');
    this.closeNavPanel = document.getElementById('closeNavPanel');
    this.switchOriginBtn = document.getElementById('switchOriginBtn');

    // Navigation State
    this.stagedDestination = null;
    this.activeDestination = null;
    this.originMode = 'gps'; // 'gps' or 'manual'
    this.manualOriginCoords = null;
    this.activeRoute = null;

    this.bindEvents();
  }

  bindEvents() {
    this.closeDestCard.addEventListener('click', () => {
      this.destCard.classList.add('hidden');
      this.stagedDestination = null;
    });

    this.startRouteBtn.addEventListener('click', () => {
      if (this.stagedDestination) {
        this.startNavigation(this.stagedDestination);
      }
    });

    this.closeNavPanel.addEventListener('click', () => {
      this.stopNavigation();
    });

    this.clearRouteBtn.addEventListener('click', () => {
      this.stopNavigation();
    });

    this.recalculateRouteBtn.addEventListener('click', () => {
      this.recalculateCurrentRoute();
    });

    this.accessibleToggle.addEventListener('change', () => {
      if (this.activeDestination) {
        this.recalculateCurrentRoute();
      }
    });

    this.switchOriginBtn.addEventListener('click', () => {
      if (this.originMode === 'gps') {
        this.originMode = 'manual';
        this.navOriginText.innerText = 'Click on map to set start';
        this.switchOriginBtn.innerText = 'Use GPS';
      } else {
        this.originMode = 'gps';
        this.navOriginText.innerText = 'My Location (GPS)';
        this.switchOriginBtn.innerText = 'Pick on Map';
        this.recalculateCurrentRoute();
      }
    });
  }

  showDestination(item) {
    this.stagedDestination = item;

    this.destTitle.innerText = item.name;
    this.destBadge.innerText = item.category || 'Location';
    this.destSubtitle.innerText = `${item.building || 'Campus'} • ${item.type.toUpperCase()}`;
    this.destDescription.innerText = item.description || 'Verified campus destination point.';

    this.destCard.classList.remove('hidden');
    this.navPanel.classList.add('hidden');

    const lat = item.coordinates?.latitude;
    const lng = item.coordinates?.longitude;
    if (lat && lng) {
      this.map.setDestinationMarker(lat, lng, item.name);
      this.map.centerOnLocation(lat, lng, 18);
    }
  }

  async startNavigation(destinationItem) {
    this.activeDestination = destinationItem;
    this.destCard.classList.add('hidden');
    this.navPanel.classList.remove('hidden');

    this.navDestinationText.innerText = destinationItem.name;

    // Trigger Geolocation if in GPS mode
    if (this.originMode === 'gps') {
      window.geoManager.startWatching();
    }

    await this.recalculateCurrentRoute();
  }

  async recalculateCurrentRoute() {
    if (!this.activeDestination) return;

    const campusId = typeof this.getCampusId === 'function' ? this.getCampusId() : this.getCampusId;
    let originCoords = null;

    if (this.originMode === 'gps') {
      const pos = window.geoManager.currentPosition;
      if (!pos) {
        this.navOriginText.innerText = 'Acquiring GPS position...';
        // Wait briefly for first fix or prompt manual
        return;
      }
      originCoords = { lat: pos.lat, lng: pos.lng };
      this.navOriginText.innerText = 'My Location (GPS)';
    } else {
      if (!this.manualOriginCoords) {
        this.navOriginText.innerText = 'Tap map to select starting point';
        return;
      }
      originCoords = this.manualOriginCoords;
      this.navOriginText.innerText = 'Manual Start Point';
    }

    const isAccessible = this.accessibleToggle.checked;
    const destPayload = {
      type: this.activeDestination.type,
      id: this.activeDestination.id,
      lat: this.activeDestination.coordinates?.latitude,
      lng: this.activeDestination.coordinates?.longitude,
    };

    try {
      this.routeDistanceDisplay.innerText = 'Calculating...';
      const route = await Api.calculateRoute(campusId, originCoords, destPayload, isAccessible);
      this.activeRoute = route;
      this.renderRoute(route);
    } catch (err) {
      console.error('Route calculation error:', err);
      this.routeDistanceDisplay.innerText = 'Error';
      this.navStepsList.innerHTML = `<li class="step-item"><span class="step-num">!</span><span>${err.message || 'Unable to calculate route.'}</span></li>`;
    }
  }

  renderRoute(route) {
    this.routeDistanceDisplay.innerText = `${Math.round(route.total_distance_meters)} m`;
    const mins = Math.max(1, Math.round(route.estimated_duration_seconds / 60));
    this.routeTimeDisplay.innerText = `~${mins} min`;

    // Render Steps
    this.navStepsList.innerHTML = '';
    (route.steps || []).forEach((step, idx) => {
      const li = document.createElement('li');
      li.className = 'step-item';
      li.innerHTML = `
        <span class="step-num">${idx + 1}</span>
        <span>${step.instruction}</span>
        <span class="step-distance">${step.distance_meters > 0 ? `${Math.round(step.distance_meters)}m` : ''}</span>
      `;
      this.navStepsList.appendChild(li);
    });

    // Draw route line on Leaflet
    if (route.geometry && route.geometry.coordinates) {
      this.map.drawRoute(route.geometry.coordinates);
    }
  }

  setManualOrigin(latlng) {
    this.manualOriginCoords = { lat: latlng.lat, lng: latlng.lng };
    this.originMode = 'manual';
    this.navOriginText.innerText = `Point (${latlng.lat.toFixed(4)}, ${latlng.lng.toFixed(4)})`;
    this.switchOriginBtn.innerText = 'Use GPS';
    if (this.activeDestination) {
      this.recalculateCurrentRoute();
    }
  }

  stopNavigation() {
    this.navPanel.classList.add('hidden');
    this.destCard.classList.add('hidden');
    this.activeDestination = null;
    this.stagedDestination = null;
    this.activeRoute = null;
    this.map.clearRoute();
  }
}

window.NavigationController = NavigationController;
