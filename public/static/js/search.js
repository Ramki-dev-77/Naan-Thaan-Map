/**
 * Campus Navigation System — Search Controller
 * Handles debounced input, category filtering, quick location labels directory, and selection.
 */

class SearchController {
  constructor(options) {
    this.searchInput = document.getElementById('searchInput');
    this.clearBtn = document.getElementById('clearSearchBtn');
    this.resultsList = document.getElementById('searchResultsList');
    this.pills = document.querySelectorAll('.category-pills .pill');
    this.spinner = document.getElementById('searchSpinner');

    this.quickLabelsSection = document.getElementById('quickLabelsSection');
    this.quickLabelsContainer = document.getElementById('quickLabelsContainer');
    this.quickLabelsCount = document.getElementById('quickLabelsCount');

    this.currentCampusId = options.getCampusId;
    this.onSelectCallback = options.onSelect;

    this.activeCategory = '';
    this.debounceTimer = null;
    this.allCampusLocations = [];
    this.selectedLocationKey = null;

    this.bindEvents();
  }

  bindEvents() {
    this.searchInput.addEventListener('input', () => {
      const val = this.searchInput.value.trim();
      if (val.length > 0) {
        this.clearBtn.classList.remove('hidden');
        if (this.quickLabelsSection) this.quickLabelsSection.classList.add('hidden');
        if (this.resultsList) this.resultsList.classList.remove('hidden');
      } else {
        this.clearBtn.classList.add('hidden');
        this.clearResults();
        if (this.quickLabelsSection) this.quickLabelsSection.classList.remove('hidden');
        if (this.resultsList) this.resultsList.classList.add('hidden');
        this.renderQuickLabels(this.activeCategory);
      }

      clearTimeout(this.debounceTimer);
      this.debounceTimer = setTimeout(() => {
        this.executeSearch();
      }, 280);
    });

    this.clearBtn.addEventListener('click', () => {
      this.searchInput.value = '';
      this.clearBtn.classList.add('hidden');
      this.clearResults();
      if (this.quickLabelsSection) this.quickLabelsSection.classList.remove('hidden');
      if (this.resultsList) this.resultsList.classList.add('hidden');
      this.renderQuickLabels(this.activeCategory);
      this.searchInput.focus();
    });

    // Category Filter Pills
    this.pills.forEach((pill) => {
      pill.addEventListener('click', () => {
        this.pills.forEach((p) => p.classList.remove('active'));
        pill.classList.add('active');
        this.activeCategory = pill.dataset.category || '';

        const query = this.searchInput.value.trim();
        if (query.length > 0) {
          this.executeSearch();
        } else {
          if (this.quickLabelsSection) this.quickLabelsSection.classList.remove('hidden');
          if (this.resultsList) this.resultsList.classList.add('hidden');
          this.renderQuickLabels(this.activeCategory);
        }
      });
    });
  }

  async loadCampusLocations(campusId) {
    if (this.spinner) this.spinner.classList.remove('hidden');
    try {
      const results = await Api.searchLocations('*', campusId, '');
      this.allCampusLocations = results || [];
      this.renderQuickLabels(this.activeCategory);
    } catch (err) {
      console.error('Error loading campus locations for sidebar:', err);
      if (this.quickLabelsCount) this.quickLabelsCount.innerText = '0 places';
    } finally {
      if (this.spinner) this.spinner.classList.add('hidden');
    }
  }

  renderQuickLabels(filterCategory = '') {
    if (!this.quickLabelsContainer) return;
    this.quickLabelsContainer.innerHTML = '';

    const cat = filterCategory.toLowerCase();
    const filtered = this.allCampusLocations.filter((item) => {
      if (!cat || cat === 'all') return true;
      const itemCat = (item.category || '').toLowerCase();
      const itemType = (item.type || '').toLowerCase();
      const itemName = (item.name || '').toLowerCase();

      if (cat === 'academic') {
        return itemType === 'building' || itemCat.includes('academic') || itemType === 'room' || itemCat.includes('lab');
      }
      if (cat === 'dining') {
        return itemCat.includes('dining') || itemName.includes('canteen') || itemName.includes('cafeteria');
      }
      if (cat === 'library') {
        return itemCat.includes('library') || itemName.includes('library');
      }
      if (cat === 'medical') {
        return itemCat.includes('medical') || itemName.includes('dispensary') || itemName.includes('clinic');
      }
      if (cat === 'parking') {
        return itemCat.includes('parking') || itemName.includes('parking');
      }
      return itemCat.includes(cat);
    });

    if (this.quickLabelsCount) {
      this.quickLabelsCount.innerText = `${filtered.length} places`;
    }

    if (filtered.length === 0) {
      this.quickLabelsContainer.innerHTML = `
        <div class="result-item" style="cursor: default; opacity: 0.7;">
          <span class="result-subtitle">No locations found in this category.</span>
        </div>
      `;
      return;
    }

    filtered.forEach((item) => {
      const card = document.createElement('div');
      const itemKey = `${item.type}_${item.id}`;
      const isSelected = (this.selectedLocationKey === itemKey);
      card.className = `location-label-card ${isSelected ? 'selected' : ''}`;
      card.dataset.key = itemKey;
      card.dataset.id = item.id;
      card.dataset.type = item.type;
      card.tabIndex = 0;
      card.setAttribute('role', 'option');

      const emoji = this.getLocationEmoji(item);
      const codeBadge = item.code ? `<span class="label-card-badge">${item.code}</span>` : '';
      const categoryName = item.category || (item.type === 'building' ? 'Campus Building' : 'Location');

      card.innerHTML = `
        <div class="label-card-icon">${emoji}</div>
        <div class="label-card-content">
          <div class="label-card-name" title="${item.name}">${item.name}</div>
          <div class="label-card-meta">
            ${codeBadge}
            <span class="label-card-cat">${categoryName}</span>
          </div>
        </div>
        <div class="label-card-action">
          <span class="label-select-btn">Select</span>
        </div>
      `;

      const selectLocation = () => {
        this.setSelectedLabel(item.id, item.type);
        if (this.onSelectCallback) {
          this.onSelectCallback(item);
        }
      };

      card.addEventListener('click', selectLocation);
      card.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          selectLocation();
        }
      });

      this.quickLabelsContainer.appendChild(card);
    });
  }

  setSelectedLabel(itemId, itemType) {
    this.selectedLocationKey = `${itemType}_${itemId}`;
    if (!this.quickLabelsContainer) return;

    const cards = this.quickLabelsContainer.querySelectorAll('.location-label-card');
    cards.forEach((card) => {
      if (card.dataset.key === this.selectedLocationKey) {
        card.classList.add('selected');
        card.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      } else {
        card.classList.remove('selected');
      }
    });
  }

  getLocationEmoji(item) {
    const type = (item.type || '').toLowerCase();
    const cat = (item.category || '').toLowerCase();
    const name = (item.name || '').toLowerCase();

    if (cat.includes('dining') || name.includes('canteen') || name.includes('cafeteria')) return '🍽️';
    if (cat.includes('library') || name.includes('library')) return '📚';
    if (cat.includes('medical') || name.includes('dispensary') || name.includes('clinic')) return '🏥';
    if (cat.includes('parking') || name.includes('parking')) return '🅿️';
    if (name.includes('hostel')) return '🛏️';
    if (name.includes('temple')) return '🛕';
    if (name.includes('gate')) return '⛩️';
    if (type === 'room') return '🚪';
    if (type === 'building') return '🏛️';
    return '📍';
  }

  async executeSearch() {
    const query = this.searchInput.value.trim();
    const campusId = typeof this.currentCampusId === 'function' ? this.currentCampusId() : this.currentCampusId;

    if (!query) {
      if (this.quickLabelsSection) this.quickLabelsSection.classList.remove('hidden');
      if (this.resultsList) this.resultsList.classList.add('hidden');
      this.renderQuickLabels(this.activeCategory);
      return;
    }

    if (this.quickLabelsSection) this.quickLabelsSection.classList.add('hidden');
    if (this.resultsList) this.resultsList.classList.remove('hidden');

    if (this.spinner) this.spinner.classList.remove('hidden');

    try {
      const results = await Api.searchLocations(query, campusId, this.activeCategory);
      this.renderResults(results);
    } catch (err) {
      console.error('Search failed:', err);
      this.resultsList.innerHTML = `<div class="result-item"><div class="result-details"><span class="result-subtitle">Error loading search results.</span></div></div>`;
    } finally {
      if (this.spinner) this.spinner.classList.add('hidden');
    }
  }

  renderResults(results) {
    if (!results || results.length === 0) {
      this.resultsList.innerHTML = `
        <div class="result-item" style="cursor: default;">
          <div class="result-details">
            <span class="result-subtitle">No matching campus locations found.</span>
          </div>
        </div>`;
      return;
    }

    this.resultsList.innerHTML = '';
    results.forEach((item) => {
      const itemEl = document.createElement('div');
      itemEl.className = 'result-item';
      itemEl.tabIndex = 0;
      itemEl.setAttribute('role', 'option');

      const emoji = this.getLocationEmoji(item);
      const iconColor = item.category_color || '#2563eb';
      const codeBadge = item.code ? `<span class="label-card-badge" style="margin-right: 4px;">${item.code}</span>` : '';
      const floorBadge = (item.floor !== null && item.floor !== undefined)
        ? `<span class="label-card-badge" style="background: #fef3c7; color: #b45309; margin-right: 4px;">Floor ${item.floor}</span>`
        : '';

      itemEl.innerHTML = `
        <div class="result-icon" style="background-color: ${iconColor};">${emoji}</div>
        <div class="result-details">
          <div class="result-title">${item.name}</div>
          <div class="result-subtitle">
            ${codeBadge}
            ${floorBadge}
            <span>${item.description || item.building || item.category}</span>
          </div>
        </div>
        <div class="label-card-action">
          <span class="label-select-btn">Select</span>
        </div>
      `;

      const selectAction = () => {
        this.clearResults();
        this.setSelectedLabel(item.id, item.type);
        if (this.onSelectCallback) {
          this.onSelectCallback(item);
        }
      };

      itemEl.addEventListener('click', selectAction);
      itemEl.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          selectAction();
        }
      });

      this.resultsList.appendChild(itemEl);
    });
  }

  clearResults() {
    this.resultsList.innerHTML = '';
  }
}

window.SearchController = SearchController;
