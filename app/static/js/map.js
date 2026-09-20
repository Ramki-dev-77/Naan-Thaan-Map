/**
 * Campus Navigation System — Map Controller
 * Encapsulates Leaflet canvas, GeoJSON rendering, custom markers, and path polylines.
 */

class CampusMap {
  constructor(elementId) {
    this.elementId = elementId;
    this.map = null;
    this.boundaryLayer = null;
    this.buildingsLayer = null;
    this.facilitiesLayer = null;
    this.walkwaysLayer = null;
    this.routePolyline = null;
    this.routeLayers = [];
    this.originMarker = null;
    this.destinationMarker = null;
    this.userMarker = null;
    this.userAccuracyCircle = null;
    this.currentCampusData = null;

    this.onFeatureSelectCallback = null;
    this.onMapClickCallback = null;
  }

  init(centerLat = 12.9722, centerLng = 77.5947, zoom = 17) {
    this.map = L.map(this.elementId, {
      center: [centerLat, centerLng],
      zoom: zoom,
      zoomControl: false,
    });

    // Top-right zoom control
    L.control.zoom({ position: 'topright' }).addTo(this.map);

    // Clean OpenStreetMap CartoDB Positron basemap
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxZoom: 20,
    }).addTo(this.map);

    // Click handler on map canvas
    this.map.on('click', (e) => {
      if (this.onMapClickCallback) {
        this.onMapClickCallback(e.latlng);
      }
    });
  }

  renderCampusData(geojsonData) {
    this.currentCampusData = geojsonData;
    this.clearLayers();

    const features = geojsonData.features || [];

    // 1. Campus Boundary
    const boundaryFeatures = features.filter((f) => f.properties.layer === 'campus_boundary');
    if (boundaryFeatures.length > 0) {
      this.boundaryLayer = L.geoJSON(boundaryFeatures, {
        style: {
          color: '#2563eb',
          weight: 2,
          opacity: 0.8,
          dashArray: '5, 5',
          fillColor: '#eff6ff',
          fillOpacity: 0.06,
        },
      }).addTo(this.map);

      this.map.fitBounds(this.boundaryLayer.getBounds(), { padding: [30, 30] });
    }

    // 2. Building Footprints (Clean vector map, no permanent pins or clutter)
    const buildingFeatures = features.filter((f) => f.properties.layer === 'building_footprint');

    this.buildingsLayer = L.geoJSON(buildingFeatures, {
      style: {
        color: '#2563eb',
        weight: 1.5,
        fillColor: '#3b82f6',
        fillOpacity: 0.16,
      },
      onEachFeature: (feature, layer) => {
        const props = feature.properties;
        layer.bindTooltip(`<strong>${props.name}</strong> (${props.code})`, {
          className: 'building-hover-tooltip',
          sticky: true,
        });

        layer.on('click', (e) => {
          if (e) L.DomEvent.stopPropagation(e);
          if (this.onFeatureSelectCallback) {
            this.onFeatureSelectCallback({
              id: props.id,
              type: 'building',
              name: props.name,
              code: props.code,
              building: props.name,
              category: 'Building',
              description: props.description,
              entrance: props.entrance,
              coordinates: {
                latitude: props.entrance?.latitude || props.latitude,
                longitude: props.entrance?.longitude || props.longitude,
              },
            });
          }
        });

        layer.on('mouseover', () => {
          layer.setStyle({ fillOpacity: 0.35, weight: 2.2, color: '#1d4ed8' });
        });
        layer.on('mouseout', () => {
          layer.setStyle({ fillOpacity: 0.16, weight: 1.5, color: '#2563eb' });
        });
      },
    }).addTo(this.map);

    // 3. Walkways (Clean pedestrian network)
    const walkwayFeatures = features.filter((f) => f.properties.layer === 'walkway');
    this.walkwaysLayer = L.geoJSON(walkwayFeatures, {
      style: (feature) => {
        const isStairs = feature.properties.stairs;
        const ptype = feature.properties.path_type;
        return {
          color: isStairs ? '#ef4444' : (ptype === 'MAIN_AVENUE' ? '#475569' : '#94a3b8'),
          weight: ptype === 'MAIN_AVENUE' ? 3 : (isStairs ? 2.5 : 2),
          opacity: ptype === 'MAIN_AVENUE' ? 0.6 : 0.45,
          dashArray: isStairs ? '3, 4' : null,
        };
      },
    }).addTo(this.map);
  }

  updateUserLocation(pos) {
    const latlng = [pos.lat, pos.lng];

    if (!this.userMarker) {
      const userHtml = `
        <div class="user-location-marker">
          <div class="user-location-dot"></div>
          <div class="user-location-pulse"></div>
        </div>`;
      const icon = L.divIcon({
        html: userHtml,
        className: 'user-marker-container',
        iconSize: [20, 20],
        iconAnchor: [10, 10],
      });
      this.userMarker = L.marker(latlng, { icon: icon, zIndexOffset: 1000 }).addTo(this.map);
    } else {
      this.userMarker.setLatLng(latlng);
    }

    // Uncertainty Radius Circle
    if (!this.userAccuracyCircle) {
      this.userAccuracyCircle = L.circle(latlng, {
        radius: pos.accuracy,
        color: pos.tierColor || '#2563eb',
        fillColor: pos.tierColor || '#2563eb',
        fillOpacity: 0.12,
        weight: 1,
      }).addTo(this.map);
    } else {
      this.userAccuracyCircle.setLatLng(latlng);
      this.userAccuracyCircle.setRadius(pos.accuracy);
      this.userAccuracyCircle.setStyle({
        color: pos.tierColor || '#2563eb',
        fillColor: pos.tierColor || '#2563eb',
      });
    }
  }

  setSelectedLocationPin(lat, lng, title = 'Selected Location', subtitle = '') {
    if (this.destinationMarker) {
      this.map.removeLayer(this.destinationMarker);
      this.destinationMarker = null;
    }

    const pinHtml = `
      <div class="google-pin-wrapper">
        <div class="google-pin-head">
          <div class="google-pin-dot"></div>
        </div>
        <div class="google-pin-shadow"></div>
      </div>
    `;

    const icon = L.divIcon({
      html: pinHtml,
      className: 'google-pin-container',
      iconSize: [36, 44],
      iconAnchor: [18, 42],
    });

    this.destinationMarker = L.marker([lat, lng], { icon: icon, zIndexOffset: 1200 }).addTo(this.map);

    const tooltipContent = subtitle
      ? `<strong>${title}</strong><br><small>${subtitle}</small>`
      : `<strong>${title}</strong>`;

    this.destinationMarker.bindTooltip(tooltipContent, {
      className: 'google-pin-tooltip',
      permanent: true,
      direction: 'top',
      offset: [0, -42],
    }).openTooltip();
  }

  setDestinationMarker(lat, lng, label = 'Destination') {
    this.setSelectedLocationPin(lat, lng, label);
  }

  setOriginMarker(lat, lng, label = 'Start Location') {
    if (this.originMarker) {
      this.map.removeLayer(this.originMarker);
      this.originMarker = null;
    }

    const originHtml = `
      <div class="origin-pin-wrapper" title="${label}">
        <div class="origin-pin-circle">
          <div class="origin-pin-inner"></div>
        </div>
      </div>
    `;

    const icon = L.divIcon({
      html: originHtml,
      className: 'origin-pin-container',
      iconSize: [24, 24],
      iconAnchor: [12, 12],
    });

    this.originMarker = L.marker([lat, lng], { icon: icon, zIndexOffset: 1100 }).addTo(this.map);
    this.originMarker.bindTooltip(`<strong>${label}</strong>`, {
      className: 'google-pin-tooltip',
      permanent: true,
      direction: 'top',
      offset: [0, -14],
    }).openTooltip();
  }

  drawRoute(geometryCoordinates) {
    this.clearRoute();
    if (!geometryCoordinates || geometryCoordinates.length === 0) return;

    const latlngs = geometryCoordinates.map((c) => [c[1], c[0]]);

    // Casing
    const casing = L.polyline(latlngs, {
      color: '#ffffff',
      weight: 10,
      opacity: 0.98,
      lineCap: 'round',
      lineJoin: 'round',
    }).addTo(this.map);

    const activeLine = L.polyline(latlngs, {
      color: '#1a73e8',
      weight: 6,
      opacity: 1.0,
      lineCap: 'round',
      lineJoin: 'round',
    }).addTo(this.map);

    const innerGlow = L.polyline(latlngs, {
      color: '#60a5fa',
      weight: 2,
      opacity: 0.8,
      lineCap: 'round',
      lineJoin: 'round',
    }).addTo(this.map);

    this.routeLayers.push(casing, activeLine, innerGlow);
    this.routePolyline = activeLine;

    this.map.fitBounds(activeLine.getBounds(), { padding: [60, 60] });
  }

  drawMultiRoutes(routes, activeRouteId, onRouteClick) {
    this.clearRoute();
    if (!routes || routes.length === 0) return;

    // Render alternative routes first so the active route stays on top
    const sorted = [...routes].sort((a, b) => (a.id === activeRouteId ? 1 : b.id === activeRouteId ? -1 : 0));
    let activeLine = null;

    sorted.forEach((route) => {
      if (!route.geometry || !route.geometry.coordinates || route.geometry.coordinates.length < 2) return;
      const latlngs = route.geometry.coordinates.map((c) => [c[1], c[0]]);
      const isActive = (route.id === activeRouteId);

      if (isActive) {
        // High visibility dual-stroke Google Maps Navigation Route:
        // 1. Soft dark drop shadow for 3D separation
        const shadow = L.polyline(latlngs, {
          color: '#0f172a',
          weight: 15,
          opacity: 0.2,
          lineCap: 'round',
          lineJoin: 'round',
        }).addTo(this.map);

        // 2. High-contrast pure white casing background
        const casing = L.polyline(latlngs, {
          color: '#ffffff',
          weight: 11,
          opacity: 1.0,
          lineCap: 'round',
          lineJoin: 'round',
        }).addTo(this.map);

        // 3. Bold Google Maps vibrant navigation blue
        activeLine = L.polyline(latlngs, {
          color: '#1a73e8',
          weight: 7,
          opacity: 1.0,
          lineCap: 'round',
          lineJoin: 'round',
        }).addTo(this.map);

        // 4. Subtle inner light ribbon
        const innerGlow = L.polyline(latlngs, {
          color: '#93c5fd',
          weight: 2.5,
          opacity: 0.9,
          lineCap: 'round',
          lineJoin: 'round',
        }).addTo(this.map);

        this.routeLayers.push(shadow, casing, activeLine, innerGlow);
        this.routePolyline = activeLine;
      } else {
        // Alternative route with white outline
        const altCasing = L.polyline(latlngs, {
          color: '#ffffff',
          weight: 7,
          opacity: 0.85,
          lineCap: 'round',
          lineJoin: 'round',
        }).addTo(this.map);

        const altLine = L.polyline(latlngs, {
          color: '#64748b',
          weight: 4.5,
          opacity: 0.75,
          dashArray: '5, 6',
          className: 'alt-route-polyline',
        }).addTo(this.map);

        altLine.bindTooltip(
          `<strong>${route.name}</strong><br><small>${route.difference || Math.round(route.total_distance_meters) + 'm'}</small><br><em>Click to choose this route</em>`,
          { sticky: true, className: 'google-pin-tooltip' }
        );

        const onAltClick = (e) => {
          L.DomEvent.stopPropagation(e);
          if (onRouteClick) onRouteClick(route.id);
        };
        altLine.on('click', onAltClick);
        altCasing.on('click', onAltClick);

        this.routeLayers.push(altCasing, altLine);
      }
    });

    if (activeLine) {
      this.map.fitBounds(activeLine.getBounds(), { padding: [70, 70], maxZoom: 18 });
    }
  }

  clearRoute() {
    if (this.routeLayers && this.routeLayers.length > 0) {
      this.routeLayers.forEach((l) => this.map.removeLayer(l));
      this.routeLayers = [];
    }
    if (this.routePolyline) {
      this.map.removeLayer(this.routePolyline);
      this.routePolyline = null;
    }
    if (this.originMarker) {
      this.map.removeLayer(this.originMarker);
      this.originMarker = null;
    }
  }

  clearSelection() {
    this.clearRoute();
    if (this.destinationMarker) {
      this.map.removeLayer(this.destinationMarker);
      this.destinationMarker = null;
    }
  }

  clearLayers() {
    if (this.boundaryLayer) this.map.removeLayer(this.boundaryLayer);
    if (this.buildingsLayer) this.map.removeLayer(this.buildingsLayer);
    if (this.walkwaysLayer) this.map.removeLayer(this.walkwaysLayer);
    this.clearSelection();
  }

  recenterCampus() {
    if (this.boundaryLayer) {
      this.map.fitBounds(this.boundaryLayer.getBounds(), { padding: [30, 30] });
    }
  }

  centerOnLocation(lat, lng, zoom = 18) {
    this.map.setView([lat, lng], zoom, { animate: true });
  }
}

window.CampusMap = CampusMap;
