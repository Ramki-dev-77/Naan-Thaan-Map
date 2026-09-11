/**
 * Campus Navigation System — Search Controller
 * Handles debounced input, category filtering, result card rendering, and selection.
 */

class SearchController {
  constructor(options) {
    this.searchInput = document.getElementById('searchInput');
    this.clearBtn = document.getElementById('clearSearchBtn');
    this.resultsList = document.getElementById('searchResultsList');
    this.pills = document.querySelectorAll('.category-pills .pill');
    this.spinner = document.getElementById('searchSpinner');

    this.currentCampusId = options.getCampusId;
    this.onSelectCallback = options.onSelect;

    this.activeCategory = '';
    this.debounceTimer = null;

    this.bindEvents();
  }

  bindEvents() {
    this.searchInput.addEventListener('input', () => {
      const val = this.searchInput.value.trim();
      if (val.length > 0) {
        this.clearBtn.classList.remove('hidden');
      } else {
        this.clearBtn.classList.add('hidden');
        this.clearResults();
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
      this.searchInput.focus();
    });

    // Category Filter Pills
    this.pills.forEach((pill) => {
      pill.addEventListener('click', () => {
        this.pills.forEach((p) => p.classList.remove('active'));
        pill.classList.add('active');
        this.activeCategory = pill.dataset.category || '';
        this.executeSearch();
      });
    });
  }

  async executeSearch() {
    const query = this.searchInput.value.trim();
    const campusId = typeof this.currentCampusId === 'function' ? this.currentCampusId() : this.currentCampusId;

    if (!query && !this.activeCategory) {
      this.clearResults();
      return;
    }

    if (this.spinner) this.spinner.classList.remove('hidden');

    try {
      const results = await Api.searchLocations(query || '*', campusId, this.activeCategory);
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

      const iconChar = item.type === 'room' ? '🚪' : (item.type === 'building' ? '🏛️' : '📍');
      const iconColor = item.category_color || '#2563eb';

      itemEl.innerHTML = `
        <div class="result-icon" style="background-color: ${iconColor};">${iconChar}</div>
        <div class="result-details">
          <div class="result-title">${item.name}</div>
          <div class="result-subtitle">${item.description || item.building || item.category}</div>
        </div>
      `;

      const selectAction = () => {
        this.clearResults();
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
