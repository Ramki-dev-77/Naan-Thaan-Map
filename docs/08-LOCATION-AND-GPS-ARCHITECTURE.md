# 08 — Location & GPS Architecture (Honest Geolocation & Indoor Limitations)

## 1. The Realities of Web-Based Geolocation
Browser geolocation (`navigator.geolocation`) relies on an unmanaged combination of:
1. **Device Satellite GNSS** (GPS, GLONASS, Galileo, BeiDou) — outdoors only with clear sky view.
2. **Wi-Fi BSSID Positioning** — indoor/urban, accuracy dependent on local router mapping databases.
3. **Cellular Tower Triangulation** — coarse positioning (accuracy often 500m – 2000m).
4. **Platform / OS Location Services** (Android Location Services, Apple CoreLocation).

### Indoor Signal Attenuation & Multipath Errors
Inside concrete and steel reinforced university structures, GNSS signals suffer severe attenuation (signal power drops by 20 to 30 dB) and multipath reflections off adjacent walls. Consequently:
- GPS signal either drops completely or drifts erratically by 30 to 80 meters.
- **Architectural Imperative**: The system **must never promise room-level GPS navigation via browser Geolocation**. Room-level precision requires verified ground truth (e.g. Wi-Fi RTT, Bluetooth Low Energy BLE beacons, or QR checkpoints).

---

## 2. Accuracy Categorization Matrix

Every geolocation coordinate emitted by the browser arrives with an `accuracy` field representing the 68% confidence radius in meters. The UI visualizes this honestly:

| Accuracy Radius | UX Tier | Color Code | UI Treatment & Behavior |
|---|---|---|---|
| **≤ 10 meters** | **Excellent** | Emerald Green (`#10b981`) | Optimal outdoor positioning. Center marker snaps cleanly to pedestrian paths. |
| **10 – 25 meters** | **Good** | Teal (`#14b8a6`) | High confidence. Translucent accuracy circle displayed. Pedestrian routing enabled. |
| **25 – 50 meters** | **Usable** | Amber (`#f59e0b`) | Acceptable confidence. Accuracy circle clearly visible. Snapping radius broadened. |
| **50 – 100 meters** | **Approximate** | Orange (`#f97316`) | Degraded confidence. Warning banner displayed: "Location is approximate." |
| **> 100 meters** | **Poor** | Crimson Red (`#ef4444`) | Severe uncertainty (cellular/coarse Wi-Fi). Route calculation prompts user: *"Your location has high uncertainty (±X m). Would you like to select your starting point manually?"* |

---

## 3. Position Smoothing & Anti-Jitter Algorithm

Raw GPS fixes exhibit rapid microscopic oscillations ("jitter") even when the user is stationary. To provide a calm user experience without introducing lag:

```
                  ┌──────────────────────────────┐
                  │ New GPS Fix (lat, lng, acc)  │
                  └──────────────┬───────────────┘
                                 │
                                 ▼
                     Is acc > 100m AND
                     previous_acc < 30m?
                                 │
                     ┌───────────┴───────────┐
                     │ YES                   │ NO
                     ▼                       ▼
            Discard as outlier      Check Velocity Jump:
            (keep previous pos)     Distance / dt > 20 m/s?
                                             │
                                 ┌───────────┴───────────┐
                                 │ YES                   │ NO
                                 ▼                       ▼
                        Discard impossible jump   Apply Exponential Moving
                        (teleportation filter)    Average (EMA, alpha = 0.35)
                                                         │
                                                         ▼
                                                  Emit Smoothed Fix
```

1. **Outlier Rejection**: If an incoming reading drops from good accuracy (<25m) to terrible accuracy (>100m) in a single reading, it is held in quarantine until confirmed by a second reading.
2. **Velocity Threshold**: Maximum human running sprint speed is ~10 m/s. Any instantaneous displacement implying velocity > 20 m/s without transit mode is flagged and clamped.
3. **Exponential Moving Average (EMA)**:
   $$\mathbf{P}_{smoothed} = \alpha \cdot \mathbf{P}_{new} + (1 - \alpha) \cdot \mathbf{P}_{previous}$$
   With $\alpha = 0.35$, visual marker position glides smoothly without lagging behind a brisk walk.

---

## 4. Privacy & Consent Protocol
1. Geolocation is **strictly on-demand**: No tracking occurs upon page load.
2. The browser prompt is triggered only when the user clicks **"My Location"** or initiates route planning from their current spot.
3. User coordinates are never transmitted to backend logging or analytics databases.
