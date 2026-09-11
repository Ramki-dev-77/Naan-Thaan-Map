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
    this.userMarker = null;
    this.userAccuracyCircle = null;
    this.destinationMarker = null;
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
          fillOpacity: 0.1,
        },
      }).addTo(this.map);

      this.map.fitBounds(this.boundaryLayer.getBounds(), { padding: [30, 30] });
    }

    // 2. Building Footprints
    const buildingFeatures = features.filter((f) => f.properties.layer === 'building_footprint');
    this.buildingsLayer = L.geoJSON(buildingFeatures, {
      style: {
        color: '#1e3a8a',
        weight: 1.5,
        fillColor: '#3b82f6',
        fillOpacity: 0.35,
      },
      onEachFeature: (feature, layer) => {
        const props = feature.properties;
        layer.bindTooltip(`<strong>${props.name}</strong> (${props.code})<br><small>${props.floors} Floors • Entrance available</small>`, {
          className: 'building-tooltip',
          sticky: true,
        });

        layer.on('mouseover', () => {
          layer.setStyle({ fillOpacity: 0.65, weight: 2.5 });
        });
        layer.on('mouseout', () => {
          layer.setStyle({ fillOpacity: 0.35, weight: 1.5 });
        });
        layer.on('click', (e) => {
          L.DomEvent.stopPropagation(e);
          if (this.onFeatureSelectCallback) {
            this.onFeatureSelectCallback({
              id: props.id,
              type: 'building',
              name: props.name,
              code: props.code,
              building: props.name,
              description: props.description,
              entrance: props.entrance,
              coordinates: {
                latitude: props.entrance.latitude,
                longitude: props.entrance.longitude,
              },
            });
          }
        });
      },
    }).addTo(this.map);

    // 3. Walkways (Pedestrian Graph)
    const walkwayFeatures = features.filter((f) => f.properties.layer === 'walkway');
    this.walkwaysLayer = L.geoJSON(walkwayFeatures, {
      style: (feature) => {
        const isStairs = feature.properties.stairs;
        return {
          color: isStairs ? '#dc2626' : '#94a3b8',
          weight: isStairs ? 2.5 : 2,
          opacity: 0.6,
          dashArray: isStairs ? '3, 4' : null,
        };
      },
    }).addTo(this.map);

    // 4. Facilities & POIs
    const facilityFeatures = features.filter((f) => f.properties.layer === 'facility');
    this.facilitiesLayer = L.geoJSON(facilityFeatures, {
      pointToLayer: (feature, latlng) => {
        const props = feature.properties;
        const iconHtml = `<div class="facility-pin" style="background-color: ${props.color || '#2563eb'};">📍</div>`;
        const customIcon = L.divIcon({
          html: iconHtml,
          className: 'facility-marker-icon',
          iconSize: [28, 28],
          iconAnchor: [14, 14],
        });

        const marker = L.marker(latlng, { icon: customIcon });
        marker.bindTooltip(`<strong>${props.name}</strong><br><small>${props.category} • ${props.opening_hours || 'Open'}</small>`, {
          className: 'building-tooltip',
        });

        marker.on('click', (e) => {
          L.DomEvent.stopPropagation(e);
          if (this.onFeatureSelectCallback) {
            this.onFeatureSelectCallback({
              id: props.id,
              type: 'facility',
              name: props.name,
              category: props.category,
              description: props.description,
              opening_hours: props.opening_hours,
              coordinates: {
                latitude: latlng.lat,
                longitude: latlng.lng,
              },
            });
          }
        });

        return marker;
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

  setDestinationMarker(lat, lng, label = 'Destination') {
    if (this.destinationMarker) {
      this.map.removeLayer(this.destinationMarker);
      this.destinationMarker = null;
    }

    const destHtml = `<div class="destination-pin"></div>`;
    const icon = L.divIcon({
      html: destHtml,
      className: 'dest-marker-container',
      iconSize: [32, 32],
      iconAnchor: [16, 32],
    });

    this.destinationMarker = L.marker([lat, lng], { icon: icon, zIndexOffset: 950 }).addTo(this.map);
    this.destinationMarker.bindTooltip(`<strong>${label}</strong>`, { className: 'building-tooltip', offset: [0, -28] }).openTooltip();
  }

  drawRoute(geometryCoordinates) {
    if (this.routePolyline) {
      this.map.removeLayer(this.routePolyline);
      this.routePolyline = null;
    }

    if (!geometryCoordinates || geometryCoordinates.length === 0) return;

    // GeoJSON coordinates are [lng, lat], Leaflet polyline requires [lat, lng]
    const latlngs = geometryCoordinates.map((c) => [c[1], c[0]]);

    this.routePolyline = L.polyline(latlngs, {
      color: '#2563eb',
      weight: 5,
      opacity: 0.9,
      lineCap: 'round',
      lineJoin: 'round',
    }).addTo(this.map);

    this.map.fitBounds(this.routePolyline.getBounds(), { padding: [50, 50] });
  }

  clearRoute() {
    if (this.routePolyline) {
      this.map.removeLayer(this.routePolyline);
      this.routePolyline = null;
    }
    if (this.destinationMarker) {
      this.map.removeLayer(this.destinationMarker);
      this.destinationMarker = null;
    }
  }

  clearLayers() {
    if (this.boundaryLayer) this.map.removeLayer(this.boundaryLayer);
    if (this.buildingsLayer) this.map.removeLayer(this.buildingsLayer);
    if (this.facilitiesLayer) this.map.removeLayer(this.facilitiesLayer);
    if (this.walkwaysLayer) this.map.removeLayer(this.walkwaysLayer);
    this.clearRoute();
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
