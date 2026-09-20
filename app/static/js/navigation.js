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
    this.routeCardsContainer = document.getElementById('routeCardsContainer');
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
    this.computedRoutes = [];
    this.activeRouteId = 'fastest';

    this.bindEvents();
  }

  bindEvents() {
    this.closeDestCard.addEventListener('click', () => {
      this.destCard.classList.add('hidden');
      this.stagedDestination = null;
      this.map.clearSelection();
      if (this.onDeselectCallback) {
        this.onDeselectCallback();
      }
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
      if (this.computedRoutes && this.computedRoutes.length > 0) {
        const targetId = this.accessibleToggle.checked ? 'accessible' : 'fastest';
        const exists = this.computedRoutes.some((r) => r.id === targetId);
        if (exists) {
          this.selectRouteById(targetId);
          return;
        }
      }
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

  getDefaultCampusOrigin(campusId) {
    if (campusId === 2) {
      const destLat = this.activeDestination?.coordinates?.latitude || this.stagedDestination?.coordinates?.latitude;
      if (destLat && destLat > 12.9878) {
        return {
          coords: { lat: 12.98550, lng: 79.97180 },
          label: 'SVCE Main Gate (NH48)',
        };
      }
      return {
        coords: { lat: 12.9880, lng: 79.9705 },
        label: 'Mens Hostel (Campus North)',
      };
    }
    return {
      coords: { lat: 12.9722, lng: 77.5947 },
      label: 'Main Campus Entrance',
    };
  }

  async showDestination(item) {
    if (!item) return;
    this.stagedDestination = item;

    this.destTitle.innerText = item.name;
    this.destBadge.innerText = item.category || 'Location';
    this.destSubtitle.innerText = `${item.building || 'Campus'} • ${(item.type || 'Point').toUpperCase()}`;
    this.destDescription.innerText = item.description || 'Verified campus destination point.';

    this.destCard.classList.remove('hidden');
    this.navPanel.classList.add('hidden');

    const lat = item.coordinates?.latitude;
    const lng = item.coordinates?.longitude;
    if (lat && lng) {
      this.map.setSelectedLocationPin(lat, lng, item.name, item.category || item.building || '');
    }

    // Immediately calculate and preview the route so it is visible right away like Google Maps!
    await this.previewRoute(item);
  }

  async previewRoute(destinationItem) {
    const campusId = typeof this.getCampusId === 'function' ? this.getCampusId() : this.getCampusId;
    let originCoords = null;
    let originLabel = 'Starting Point';

    if (this.originMode === 'manual' && this.manualOriginCoords) {
      originCoords = this.manualOriginCoords;
      originLabel = 'Manual Start Point';
    } else {
      const pos = window.geoManager.currentPosition;
      if (pos && pos.lat && pos.lng) {
        originCoords = { lat: pos.lat, lng: pos.lng };
        originLabel = 'My Location (GPS)';
      } else {
        const def = this.getDefaultCampusOrigin(campusId);
        originCoords = def.coords;
        originLabel = def.label;
      }
    }

    this.currentOriginCoords = originCoords;
    this.map.setOriginMarker(originCoords.lat, originCoords.lng, originLabel);

    const destPayload = {
      type: destinationItem.type,
      id: destinationItem.id,
      lat: destinationItem.coordinates?.latitude,
      lng: destinationItem.coordinates?.longitude,
    };

    try {
      const isAccessible = this.accessibleToggle ? this.accessibleToggle.checked : false;
      const routeData = await Api.calculateRoute(campusId, originCoords, destPayload, isAccessible);
      this.activeRoute = routeData;
      this.computedRoutes = routeData.routes || [routeData];
      this.activeRouteId = routeData.active_route_id || 'fastest';

      this.map.drawMultiRoutes(this.computedRoutes, this.activeRouteId, (clickedId) => {
        this.selectRouteById(clickedId);
      });
    } catch (err) {
      console.warn('[Route Preview]', err.message);
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
      if (pos && pos.lat && pos.lng) {
        originCoords = { lat: pos.lat, lng: pos.lng };
        this.navOriginText.innerText = 'My Location (GPS)';
      } else {
        const def = this.getDefaultCampusOrigin(campusId);
        originCoords = def.coords;
        this.navOriginText.innerText = def.label;
      }
    } else {
      if (!this.manualOriginCoords) {
        const def = this.getDefaultCampusOrigin(campusId);
        originCoords = def.coords;
        this.navOriginText.innerText = def.label;
      } else {
        originCoords = this.manualOriginCoords;
        this.navOriginText.innerText = 'Manual Start Point';
      }
    }

    this.currentOriginCoords = originCoords;

    const isAccessible = this.accessibleToggle.checked;
    const destPayload = {
      type: this.activeDestination.type,
      id: this.activeDestination.id,
      lat: this.activeDestination.coordinates?.latitude,
      lng: this.activeDestination.coordinates?.longitude,
    };

    try {
      this.routeDistanceDisplay.innerText = 'Calculating...';
      const routeData = await Api.calculateRoute(campusId, originCoords, destPayload, isAccessible);
      this.activeRoute = routeData;
      this.computedRoutes = routeData.routes || [routeData];
      this.activeRouteId = routeData.active_route_id || (isAccessible ? 'accessible' : 'fastest');

      this.renderRouteSelection(this.computedRoutes, this.activeRouteId);
    } catch (err) {
      console.error('Route calculation error:', err);
      this.routeDistanceDisplay.innerText = 'Error';
      this.navStepsList.innerHTML = `<li class="step-item"><span class="step-num">!</span><span>${err.message || 'Unable to calculate route.'}</span></li>`;
      if (this.routeCardsContainer) {
        this.routeCardsContainer.innerHTML = '';
      }
    }
  }

  renderRouteSelection(routes, activeRouteId) {
    const activeRoute = routes.find((r) => r.id === activeRouteId) || routes[0];
    if (!activeRoute) return;

    // Header metrics
    this.routeDistanceDisplay.innerText = `${Math.round(activeRoute.total_distance_meters)} m`;
    const mins = Math.max(1, Math.round(activeRoute.estimated_duration_seconds / 60));
    this.routeTimeDisplay.innerText = `~${mins} min`;

    // Drop Origin Pin at starting point
    if (this.currentOriginCoords) {
      const originLabel = (this.originMode === 'gps') ? 'My Location (GPS)' : 'Starting Point';
      this.map.setOriginMarker(this.currentOriginCoords.lat, this.currentOriginCoords.lng, originLabel);
    }

    // Drop Destination Pin at ending point
    const destLat = this.activeDestination?.coordinates?.latitude;
    const destLng = this.activeDestination?.coordinates?.longitude;
    if (destLat && destLng) {
      this.map.setSelectedLocationPin(
        destLat,
        destLng,
        this.activeDestination.name,
        this.activeDestination.category || this.activeDestination.building || ''
      );
    }

    // Render Route Comparison Cards
    if (this.routeCardsContainer) {
      this.routeCardsContainer.innerHTML = '';

      routes.forEach((r) => {
        const isSelected = (r.id === activeRouteId);
        const card = document.createElement('div');
        card.className = `route-card ${isSelected ? 'selected' : ''}`;

        let icon = '⚡';
        let badgeClass = 'fastest';
        if (r.id === 'accessible') {
          icon = '♿';
          badgeClass = 'step-free';
        } else if (r.id === 'main_avenue') {
          icon = '🌳';
          badgeClass = 'main-avenue';
        }

        const rMins = Math.max(1, Math.round(r.estimated_duration_seconds / 60));

        card.innerHTML = `
          <div class="route-card-header">
            <div class="route-card-name-group">
              <span class="route-card-icon">${icon}</span>
              <span class="route-card-name">${r.name}</span>
              <span class="route-card-badge ${badgeClass}">${r.badge || r.name}</span>
            </div>
            <div class="route-card-metrics">
              <span>${Math.round(r.total_distance_meters)}m</span>
              <span class="route-card-time">~${rMins}m</span>
            </div>
          </div>
          <div class="route-card-diff">
            <span>${r.difference || r.description}</span>
          </div>
        `;

        card.addEventListener('click', () => {
          this.selectRouteById(r.id);
        });

        this.routeCardsContainer.appendChild(card);
      });
    }

    // Render Turn-by-Turn Steps
    this.navStepsList.innerHTML = '';
    (activeRoute.steps || []).forEach((step, idx) => {
      const li = document.createElement('li');
      li.className = 'step-item';
      li.innerHTML = `
        <span class="step-num">${idx + 1}</span>
        <span>${step.instruction}</span>
        <span class="step-distance">${step.distance_meters > 0 ? `${Math.round(step.distance_meters)}m` : ''}</span>
      `;
      this.navStepsList.appendChild(li);
    });

    // Draw all routes with active route highlighted in bright color and alternatives clickable
    this.map.drawMultiRoutes(this.computedRoutes, this.activeRouteId, (clickedId) => {
      this.selectRouteById(clickedId);
    });
  }

  selectRouteById(routeId) {
    if (!this.computedRoutes || this.computedRoutes.length === 0) return;
    this.activeRouteId = routeId;

    // Synchronize accessible switch visual state
    if (routeId === 'accessible') {
      this.accessibleToggle.checked = true;
    } else if (routeId === 'fastest') {
      this.accessibleToggle.checked = false;
    }

    this.renderRouteSelection(this.computedRoutes, this.activeRouteId);
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
    this.computedRoutes = [];
    this.currentOriginCoords = null;
    this.map.clearSelection();
    if (this.onDeselectCallback) {
      this.onDeselectCallback();
    }
  }
}

window.NavigationController = NavigationController;
