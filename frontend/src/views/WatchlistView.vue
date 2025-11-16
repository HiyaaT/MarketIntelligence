<script setup>
import { ref, computed, watch } from 'vue'
import { useAuthStore } from '@/stores/auth_store'
import { useMessageStore } from '@/stores/message_store'


// --- Initialize Stores ---
const authStore = useAuthStore()
const messageStore = useMessageStore()

// --- Reactive State ---
const watchlist = ref([])
const watchlistLoading = ref(false)
const watchlistError = ref(null)

// Monte Carlo modal state
const showMonteCarloModal = ref(false)
const monteCarloData = ref(null)
const monteLoading = ref(false)
const monteError = ref(null)

// NEW: Technical Signal modal state
const showSignalModal = ref(false)
const signalData = ref(null) // Corrected initialization
const signalLoading = ref(false)
const signalError = ref(null)

// --- Computed Properties ---
const backendURL = computed(() => authStore.getBackendServerURL())
const token = computed(() => authStore.getToken())
const userId = computed(() => authStore.getUserId())

/**
 * Converts the complex signal string (e.g., "Neutral to Bullish")
 * into a valid CSS class name (e.g., "neutral-to-bullish").
 * @param {string} signal The signal string from the API.
 * @returns {string} The CSS class name.
 */
const signalClass = computed(() => {
  if (!signalData.value || !signalData.value.signal) return ''
  return signalData.value.signal.toLowerCase().replace(/\s/g, '-').replace(/\(|\)/g, '')
})

// --- Helper Functions ---
function getAuthHeaders() {
  const headers = { 'Content-Type': 'application/json' }
  if (token.value) headers['Authorization'] = `Bearer ${token.value}`
  return headers
}

// --- Fetch Watchlist ---
async function fetchWatchlist() {
  if (!userId.value) return
  watchlistLoading.value = true
  watchlistError.value = null

  try {
    const url = `${backendURL.value}/api/v1/watchlist/${userId.value}`
    const res = await fetch(url, { headers: getAuthHeaders() })

    if (!res.ok) throw new Error('Failed to fetch watchlist')

    const data = await res.json()
    // Ensure price is treated as a number for .toFixed() in template
    watchlist.value = (data.watchlist || []).map(item => ({
        ...item,
        price: Number(item.price) // Ensure price is number
    }))
  } catch (err) {
    watchlistError.value = err.message
    messageStore.setFlashMessage(`Error: ${err.message}`)
  } finally {
    watchlistLoading.value = false
  }
}

// --- Delete from Watchlist ---
async function deleteFromWatchlist(id, ticker) {
  try {
    const url = `${backendURL.value}/api/v1/watchlist/${id}`
    const res = await fetch(url, { method: 'DELETE', headers: getAuthHeaders() })

    if (!res.ok) throw new Error(`Failed to delete ${ticker}`)

    watchlist.value = watchlist.value.filter(i => i.id !== id)
    messageStore.setFlashMessage(`Removed ${ticker} from watchlist`)
  } catch (err) {
    messageStore.setFlashMessage(`Error: ${err.message}`)
  }
}

// --- Monte Carlo Prediction ---
async function predictMonteCarlo() {
  if (!watchlist.value.length) return

  monteLoading.value = true
  monteError.value = null
  monteCarloData.value = null
  showMonteCarloModal.value = true

  try {
    const stocks = watchlist.value.map(s => s.ticker)

    const res = await fetch(`${backendURL.value}/api/v1/montecarlo`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ stocks })
    })

    const data = await res.json()
    if (!res.ok || data.error) throw new Error(data.error || 'Monte Carlo simulation failed')

    // Map API keys to template-friendly keys
    monteCarloData.value = {
      stocks: data.stocks || stocks,
      expected_return: Number(data.expected_return_percent ?? 0),
      volatility: Number(data.volatility_percent ?? 0),
      worst_5_percent: Number(data.worst_5_percent_percent ?? 0),
      conclusion: data.conclusion || 'No conclusion'
    }
  } catch (err) {
    monteError.value = err.message || 'Monte Carlo simulation failed'
  } finally {
    monteLoading.value = false
  }
}

// --- NEW: Get Technical Signal ---
async function getTechnicalSignal(ticker) {
  signalLoading.value = true
  signalError.value = null
  signalData.value = null
  showSignalModal.value = true // Show modal immediately

  try {
    // IMPORTANT: Path must match your Flask resource definition
    const url = `${backendURL.value}/api/v1/technical_signal?stock=${ticker}`
    const res = await fetch(url, { headers: getAuthHeaders() })

    const data = await res.json()
    if (!res.ok || data.error) throw new Error(data.error || 'Failed to fetch signal')

    signalData.value = data
  } catch (err) {
    signalError.value = err.message || `Failed to get signal for ${ticker}`
  } finally {
    signalLoading.value = false
  }
}

// --- Watch userId changes ---
watch(userId, (id) => {
  if (id) fetchWatchlist()
}, { immediate: true })
</script>

<template>
  <div class="watchlist-view">
    <div class="header-section">
      <h2 class="title">Your Watchlist ({{ watchlist.length }} stocks)</h2>
      <button
        v-if="watchlist.length > 0"
        @click="predictMonteCarlo"
        class="run-monte-carlo-btn"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-play-btn" viewBox="0 0 16 16">
          <path d="M6.79 5.093A.5.5 0 0 0 6 5.5v5a.5.5 0 0 0 .79.407l3.5-2.5a.5.5 0 0 0 0-.814z"/>
          <path d="M0 4a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2zm15 0a1 1 0 0 0-1-1H2a1 1 0 0 0-1 1v8a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1z"/>
        </svg>
        Run Monte Carlo Simulation
      </button>
    </div>

    <div v-if="watchlistLoading">Fetching Data...</div>
    <div v-else-if="watchlistError" class="error">{{ watchlistError }}</div>
    <div v-else-if="!watchlist.length" class="empty">No items in watchlist.</div>

    <ul v-else class="list">
      <li v-for="item in watchlist" :key="item.id" class="stock-item-card">
        
        <div class="stock-info-main">
          <div class="ticker-and-change">
            <span class="ticker-name">{{ item.ticker }}</span>
            <span :class="['percentage-change', item.change_direction === 'up' ? 'positive' : 'negative']">
              <span v-if="item.change_direction === 'up'">▲</span>
              <span v-else-if="item.change_direction === 'down'">▼</span>
              {{ item.percentage_change }}%
            </span>
          </div>
          <span class="company-name">{{ item.company_name }}</span>
          <div class="price-info">
            <span class="label">Price</span>
            <span class="value">{{ item.price.toFixed(2) }}</span>
          </div>
        </div>

        <div class="stock-details">
          <div class="detail-group">
            <span class="label">Market Cap</span>
            <span class="value">{{ item.market_cap }}</span>
          </div>
          <div class="detail-group">
            <span class="label">Volume</span>
            <span class="value">{{ item.volume }}</span>
          </div>
          <div class="detail-group">
            <span class="label">P/E Ratio</span>
            <span class="value">{{ item.pe_ratio }}</span>
          </div>
        </div>

        <div class="actions">
          <button @click="getTechnicalSignal(item.ticker)" class="btn-action bullish-bearish">
            Bullish/Bearish
          </button>
          <button @click="deleteFromWatchlist(item.id, item.ticker)" class="btn-delete">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-trash" viewBox="0 0 16 16">
              <path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5m2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5m3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0z"/>
              <path d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H3a1 1 0 0 1 1-1h8a1 1 0 0 1 1 1h1.5a1 1 0 0 1 1 1zM2.5 3h11V2h-11z"/>
            </svg>
          </button>
        </div>
      </li>
    </ul>

    <div
      v-if="showMonteCarloModal"
      class="modal-backdrop"
      @click.self="showMonteCarloModal = false"
    >
      <div class="modal-content">
        <h3>Monte Carlo Portfolio Simulation</h3>
        <div v-if="monteLoading">Simulating...</div>
        <div v-else-if="monteError" class="error">{{ monteError }}</div>
        <div v-else-if="monteCarloData">
          <p><strong>Stocks:</strong> {{ monteCarloData.stocks.join(', ') }}</p>
          <p><strong>Expected Return:</strong> {{ monteCarloData.expected_return }}%</p>
          <p><strong>Volatility:</strong> {{ monteCarloData.volatility }}%</p>
          <p><strong>Worst 5%:</strong> {{ monteCarloData.worst_5_percent }}%</p>
          <p><strong>Conclusion:</strong> {{ monteCarloData.conclusion }}</p>
        </div>
        <button @click="showMonteCarloModal = false" class="btn-close">Close</button>
      </div>
    </div>

    <div
      v-if="showSignalModal"
      class="modal-backdrop"
      @click.self="showSignalModal = false"
    >
      <div class="modal-content signal-modal">
        <h3>Technical Signal Analysis</h3>
        <div v-if="signalLoading">Analyzing Stock Data...</div>
        <div v-else-if="signalError" class="error">{{ signalError }}</div>
        <div v-else-if="signalData">
          <h4>{{ signalData.ticker }}</h4>
          <p><strong>Price:</strong> ₹{{ signalData.current_price.toFixed(2) }}</p>
          <div :class="['signal-box', signalClass]">
            <strong>Signal: {{ signalData.signal }}</strong>
            <p class="action-text">
              **{{ signalData.suggested_action }}**
            </p>
          </div>
          <p class="commentary">{{ signalData.commentary }}</p>
        </div>
        <button @click="showSignalModal = false" class="btn-close">Close</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* GENERAL LAYOUT AND HEADER */
.watchlist-view {
  font-family: sans-serif; 
  background-color: #f7f8fc; 
  padding: 1.5rem;
}

.header-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.title {
  font-size: 1.25rem; 
  font-weight: 600; 
  color: #333;
  margin: 0;
}

.run-monte-carlo-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background-color: #8a48f7; /* Purple */
  color: white;
  border: none;
  border-radius: 0.5rem;
  padding: 0.6rem 1rem;
  font-size: 0.9rem;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.run-monte-carlo-btn:hover {
  background-color: #7234d7;
}

.run-monte-carlo-btn svg {
  fill: currentColor;
}

.list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column; 
  gap: 1rem;
}

/* STOCK CARD STYLING */
.stock-item-card {
  background: white;
  border-radius: 0.75rem;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
  padding: 1.2rem 1.5rem;
  
  /* Use CSS Grid for the card layout */
  display: grid; 
  grid-template-columns: 1.2fr 2fr 1fr; /* Main Info | Details | Actions */
  align-items: center;
  gap: 1.5rem; 
}

/* LEFT SECTION: Ticker, Name, Price */
.stock-info-main {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.ticker-and-change {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.ticker-name {
  font-size: 1.1rem;
  font-weight: 700;
  color: #333;
}

.company-name {
  font-size: 0.85rem;
  color: #718096;
}

.price-info {
  margin-top: 0.5rem;
}

/* Price Change Chip */
.percentage-change {
  display: inline-flex;
  align-items: center;
  padding: 0.2rem 0.4rem;
  border-radius: 0.3rem;
  font-size: 0.8rem;
  font-weight: 600;
  white-space: nowrap;
}

.percentage-change.positive {
  background-color: #e6ffed; /* Light green */
  color: #276749; /* Darker green */
}

.percentage-change.negative {
  background-color: #fff0f0; /* Light red */
  color: #9b2c2c; /* Darker red */
}


/* MIDDLE SECTION: Details Grid */
.stock-details {
  display: flex;
  justify-content: space-around;
  text-align: left;
}

.detail-group {
  display: flex;
  flex-direction: column;
  flex: 1;
}

.label {
  font-size: 0.8rem;
  color: #a0aec0;
  margin-bottom: 0.1rem;
}

.value {
  font-size: 0.95rem;
  font-weight: 500;
  color: #4a5568;
}

/* RIGHT SECTION: Actions */
.actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 0.5rem;
}

.btn-action {
  background-color: #e6f0ff; 
  color: #3b82f6; 
  border: none;
  border-radius: 0.3rem;
  padding: 0.5rem 0.8rem;
  font-size: 0.85rem;
  cursor: pointer;
  transition: background-color 0.2s ease;
  white-space: nowrap;
}

.btn-action:hover {
  background-color: #cce0ff;
}

.btn-delete {
  background: #fdf2f2;
  border: none;
  color: #ef4444;
  width: 35px;
  height: 35px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.btn-delete:hover {
  background-color: #ffe0e0;
}

.btn-delete svg {
  fill: currentColor;
}


/* MODAL STYLES (Kept from original) */
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 50;
}

.modal-content {
  background: white;
  padding: 1.5rem;
  border-radius: 0.75rem;
  width: 350px;
  max-width: 90%;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.btn-close {
  margin-top: 1rem;
  background: #ef4444;
  color: white;
  border: none;
  border-radius: 0.5rem;
  padding: 0.5rem 1rem;
  cursor: pointer;
}

.error {
  color: #ef4444;
}

.empty {
  text-align: center;
  padding: 2rem;
  background-color: #fff;
  border-radius: 0.75rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  color: #555;
}


/* Signal Box Styles */
.signal-box {
  margin: 1rem 0;
  padding: 1rem;
  border-radius: 0.5rem;
  text-align: center;
}

.strong-bullish, .bullish-weak, .neutral-to-bullish {
  background-color: #e6ffed; 
  border: 1px solid #48bb78; 
  color: #276749;
}

.strong-bearish, .bearish-weak, .neutral-to-bearish {
  background-color: #fff5f5; 
  border: 1px solid #f56565; 
  color: #9b2c2c;
}

.neutral {
  background-color: #f7fafc; 
  border: 1px solid #a0aec0; 
  color: #4a5568;
}

.strong-bullish {
  box-shadow: 0 0 5px rgba(72, 187, 120, 0.5);
}

.strong-bearish {
  box-shadow: 0 0 5px rgba(245, 101, 101, 0.5);
}

.action-text {
  font-size: 1.1rem;
  margin-top: 0.5rem;
}

.commentary {
  font-size: 0.9rem;
  color: #718096;
  margin-top: 1rem;
  border-top: 1px dashed #e2e8f0;
  padding-top: 0.5rem;
}
</style>