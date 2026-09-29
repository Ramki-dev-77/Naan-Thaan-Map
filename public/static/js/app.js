/**
 * Campus Navigation System — Main Application Orchestrator
 * Bootstraps map, search, geolocation, and navigation lifecycle.
 */

document.addEventListener('DOMContentLoaded', async () => {
  const campusSelect = document.getElementById('campusSelect');
  const myLocationBtn = document.getElementById('myLocationBtn');
  const recenterCampusBtn = document.getElementById('recenterCampusBtn');
  const gpsAlertBanner = document.getElementById('gpsAlertBanner');
  const dismissGpsAlert = document.getElementById('dismissGpsAlert');
  const accuracyDot = document.getElementById('accuracyDot');
  const accuracyText = document.getElementById('accuracyText');

  // 1. Initialize Map
  const campusMap = new CampusMap('map');
  campusMap.init();

  const getActiveCampusId = () => {
    return parseInt(campusSelect.value, 10) || 1;
  };

  // 2. Initialize Navigation Controller
  const navCtrl = new NavigationController({
    map: campusMap,
    getCampusId: getActiveCampusId,
  });

  // 3. Initialize Search Controller
  const searchCtrl = new SearchController({
    getCampusId: getActiveCampusId,
    onSelect: (item) => {
      navCtrl.showDestination(item);
    },
  });

  navCtrl.onDeselectCallback = () => {
    searchCtrl.setSelectedLabel(null, null);
  };

  // 4. Map feature selection callback (clicking building/facility on map)
  campusMap.onFeatureSelectCallback = (item) => {
    navCtrl.showDestination(item);
    if (item.id && item.type) {
      searchCtrl.setSelectedLabel(item.id, item.type);
    }
  };

  // 5. Map canvas click (Google Maps style: clicking anywhere drops a pin and shows destination card)
  campusMap.onMapClickCallback = (latlng) => {
    if (navCtrl.originMode === 'manual') {
      navCtrl.setManualOrigin(latlng);
      return;
    }

    navCtrl.showDestination({
      id: null,
      type: 'map_point',
      name: 'Selected Location',
      building: 'Campus Map',
      category: 'Dropped Pin',
      description: `Coordinates: ${latlng.lat.toFixed(5)}, ${latlng.lng.toFixed(5)}`,
      coordinates: {
        latitude: latlng.lat,
        longitude: latlng.lng,
      },
    });
  };

  // 6. Load Campus Data Function
  const loadCampus = async (campusId) => {
    try {
      const geojsonData = await Api.getCampusMapData(campusId);
      campusMap.renderCampusData(geojsonData);
      await searchCtrl.loadCampusLocations(campusId);
    } catch (err) {
      console.error('Error loading campus map data:', err);
    }
  };

  // Listen to campus selector changes
  campusSelect.addEventListener('change', () => {
    const campusId = getActiveCampusId();
    navCtrl.stopNavigation();
    loadCampus(campusId);
  });

  // Initial Load
  const initialCampusId = getActiveCampusId();
  if (initialCampusId) {
    await loadCampus(initialCampusId);
  }

  // 7. Geolocation Integration
  window.geoManager.onPositionUpdate((pos) => {
    campusMap.updateUserLocation(pos);

    // Update Accuracy Readout in Navigation UI
    if (accuracyDot && accuracyText) {
      accuracyDot.className = `accuracy-dot ${pos.tier}`;
      accuracyText.innerText = `Accuracy: ±${pos.accuracy}m (${pos.tierLabel})`;
    }

    // Honest Indoor Warning Banner: show when accuracy > 50m (approximate or poor)
    if (pos.accuracy > 50 && gpsAlertBanner.classList.contains('hidden')) {
      gpsAlertBanner.classList.remove('hidden');
    }

    // Auto-recalculate if user is actively navigating and in GPS mode
    if (navCtrl.activeDestination && navCtrl.originMode === 'gps' && navCtrl.activeRoute) {
      // Check if distance to current route polyline exceeds threshold (25m)
      // If position has moved significantly, trigger recalculation
      if (!navCtrl.lastNavRecalcTime || Date.now() - navCtrl.lastNavRecalcTime > 8000) {
        navCtrl.lastNavRecalcTime = Date.now();
        navCtrl.recalculateCurrentRoute();
      }
    }
  });

  window.geoManager.onError((err) => {
    console.warn('[GPS Error]', err.message);
    if (accuracyText) {
      accuracyText.innerText = 'GPS: Unavailable';
    }
    if (gpsAlertBanner) {
      gpsAlertBanner.classList.remove('hidden');
    }
  });

  // Floating Control Handlers
  myLocationBtn.addEventListener('click', () => {
    myLocationBtn.classList.add('active');
    window.geoManager.startWatching();

    const currentPos = window.geoManager.currentPosition;
    if (currentPos) {
      campusMap.centerOnLocation(currentPos.lat, currentPos.lng, 18);
    }
  });

  recenterCampusBtn.addEventListener('click', () => {
    campusMap.recenterCampus();
  });

  if (dismissGpsAlert) {
    dismissGpsAlert.addEventListener('click', () => {
      gpsAlertBanner.classList.add('hidden');
    });
  }
});
