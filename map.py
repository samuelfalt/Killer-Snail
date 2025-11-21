import argparse
from http.server import HTTPServer, SimpleHTTPRequestHandler
from typing import Tuple


HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>My Location Map</title>
  <link
    rel="stylesheet"
    href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
  />
  <style>
    :root {
      --bg: #0b1623;
      --panel: #0f2238;
      --accent: #22c55e;
      --text: #e6f0ff;
      --muted: #9fb3c8;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: radial-gradient(120% 120% at 20% 20%, #123055, #0b1623 55%);
      color: var(--text);
      min-height: 100vh;
      display: grid;
      grid-template-rows: auto 1fr;
    }
    header {
      padding: 18px 20px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      background: linear-gradient(90deg, #0f2238, rgba(15, 34, 56, 0.75));
      border-bottom: 1px solid rgba(255, 255, 255, 0.06);
      box-shadow: 0 10px 40px rgba(0, 0, 0, 0.35);
    }
    h1 {
      margin: 0;
      font-size: 18px;
      letter-spacing: 0.03em;
      text-transform: uppercase;
      color: var(--text);
    }
    .controls {
      display: flex;
      align-items: center;
      gap: 10px;
      color: var(--muted);
      font-size: 14px;
      padding: 6px 10px;
      background: rgba(255, 255, 255, 0.04);
      border-radius: 12px;
      border: 1px solid rgba(255, 255, 255, 0.06);
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
    }
    .controls input[type="range"] {
      accent-color: var(--accent);
    }
    .btn {
      padding: 7px 12px;
      border-radius: 10px;
      border: 1px solid rgba(255, 255, 255, 0.12);
      background: linear-gradient(135deg, rgba(34, 197, 94, 0.16), rgba(34, 197, 94, 0.38));
      color: var(--text);
      font-weight: 600;
      cursor: pointer;
      transition: transform 120ms ease, box-shadow 120ms ease;
    }
    .btn:hover {
      transform: translateY(-1px);
      box-shadow: 0 6px 18px rgba(0, 0, 0, 0.25);
    }
    .snail-icon {
      font-size: 34px;
      line-height: 1;
      text-align: center;
      filter: drop-shadow(0 4px 8px rgba(0,0,0,0.35));
      user-select: none;
    }
    .status {
      margin: 0;
      font-size: 14px;
      color: var(--muted);
    }
    .pill {
      padding: 6px 10px;
      border-radius: 999px;
      background: rgba(34, 197, 94, 0.15);
      color: var(--accent);
      font-weight: 600;
      letter-spacing: 0.02em;
      border: 1px solid rgba(34, 197, 94, 0.35);
    }
    #map {
      width: 100%;
      height: calc(100vh - 70px);
      filter: drop-shadow(0 10px 30px rgba(0,0,0,0.35));
    }
    .overlay {
      position: fixed;
      inset: 70px 0 0 0;
      background: rgba(11, 22, 35, 0.9);
      backdrop-filter: blur(10px);
      display: grid;
      place-items: center;
      z-index: 10;
      padding: 24px;
    }
    .overlay.hidden { display: none; }
    .panel {
      width: min(900px, 96vw);
      background: rgba(15, 34, 56, 0.9);
      border: 1px solid rgba(255,255,255,0.08);
      border-radius: 20px;
      padding: 22px 22px 18px;
      box-shadow: 0 25px 60px rgba(0,0,0,0.45);
    }
    .panel h2 {
      margin: 0 0 10px;
      letter-spacing: 0.02em;
      font-size: 20px;
    }
    .choice-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
      gap: 12px;
      margin: 14px 0 10px;
    }
    .card {
      background: rgba(255,255,255,0.04);
      border: 1px solid rgba(255,255,255,0.08);
      border-radius: 14px;
      padding: 12px;
      cursor: pointer;
      transition: transform 120ms ease, border-color 120ms ease, box-shadow 120ms ease;
    }
    .card:hover { transform: translateY(-2px); border-color: rgba(34, 197, 94, 0.5); }
    .card.active {
      border-color: rgba(34,197,94,0.9);
      box-shadow: 0 12px 28px rgba(0,0,0,0.28);
    }
    .card .emoji { font-size: 28px; display: block; }
    .card .name { font-weight: 700; margin: 6px 0 2px; }
    .card .speed { color: var(--muted); font-size: 13px; }
    .start-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin-top: 6px;
    }
    .start-btn {
      padding: 10px 16px;
      border-radius: 12px;
      border: none;
      background: linear-gradient(135deg, #22c55e, #16a34a);
      color: #0b1623;
      font-weight: 800;
      letter-spacing: 0.02em;
      cursor: pointer;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.32);
      transition: transform 120ms ease, box-shadow 120ms ease;
    }
    .start-btn:hover { transform: translateY(-2px); box-shadow: 0 12px 32px rgba(0,0,0,0.36); }
    #message {
      position: fixed;
      bottom: 14px;
      left: 50%;
      transform: translateX(-50%);
      background: rgba(15, 34, 56, 0.95);
      color: var(--text);
      padding: 10px 14px;
      border-radius: 12px;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.38);
      font-size: 14px;
      border: 1px solid rgba(255, 255, 255, 0.08);
      max-width: 90vw;
    }
  </style>
</head>
<body>
  <header>
    <div>
      <h1>Live Location</h1>
      <p class="status" id="status">Waiting for location permission…</p>
    </div>
    <div class="controls">
      <label for="speed">Snail speed</label>
      <input id="speed" type="range" min="0" max="10" step="0.5" value="2" aria-label="Snail speed in km per hour" />
      <span id="speed-value">2.0</span><span>km/h</span>
      <button id="restart-snail" class="btn" type="button">Reset</button>
      <button id="open-selection" class="btn" type="button">Change character</button>
    </div>
    <div class="pill" id="pill">Idle</div>
  </header>
  <div id="map" role="region" aria-label="Map showing your location"></div>
  <div class="overlay" id="start-overlay">
    <div class="panel">
      <h2>Pick your chaser</h2>
      <div class="choice-grid" id="character-grid"></div>
      <div class="start-row">
        <p class="status" id="selected-label">Selected: Snail · 0.048 km/h</p>
        <button id="start-btn" class="start-btn" type="button">Start chase</button>
      </div>
    </div>
  </div>
  <div id="message" aria-live="polite">Enable location services to see your position.</div>

  <script
    src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
  ></script>
  <script>
    const statusEl = document.getElementById("status");
    const pillEl = document.getElementById("pill");
    const messageEl = document.getElementById("message");
    const speedInput = document.getElementById("speed");
    const speedValue = document.getElementById("speed-value");
    const restartBtn = document.getElementById("restart-snail");
    const openSelectionBtn = document.getElementById("open-selection");
    const overlay = document.getElementById("start-overlay");
    const characterGrid = document.getElementById("character-grid");
    const startBtn = document.getElementById("start-btn");
    const selectedLabel = document.getElementById("selected-label");

    let userCoords = null;
    let snailCoords = null;
    let userMarker = null;
    let snailMarker = null;
    let accuracyCircle = null;
    let speedKmh = parseFloat(speedInput.value);
    let selectedCharId = "snail";
    let gameStarted = false;
    let selectedEmoji = "🐌";

    const map = L.map("map", { zoomControl: true, worldCopyJump: true });
    const tileLayer = L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors'
    });
    tileLayer.addTo(map);
    map.setView([0, 0], 2);

    const markerIcon = L.icon({
      iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
      shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
      iconAnchor: [12, 41],
      popupAnchor: [0, -32]
    });

    const characters = [
      { id: "snail", emoji: "🐌", name: "Snail", speed: 0.048, min: 0.048, max: 0.048, adjustable: false },
      { id: "frog", emoji: "🐸", name: "Frog", speed: 1, min: 1, max: 1, adjustable: false },
      { id: "tiger", emoji: "🐯", name: "Tiger", speed: 50, min: 50, max: 50, adjustable: false },
      { id: "ninja", emoji: "🥷🏻", name: "Ninja", speed: 5, min: 2, max: 25, adjustable: true },
    ];

    function setStatus(text, pill) {
      statusEl.textContent = text;
      pillEl.textContent = pill;
    }

    function updateMessage(text) {
      messageEl.textContent = text;
    }

    function setCharacter(id) {
      const choice = characters.find(c => c.id === id) || characters[0];
      selectedCharId = choice.id;
      selectedEmoji = choice.emoji;
      speedKmh = choice.speed;
      speedInput.min = choice.min;
      speedInput.max = choice.max;
      speedInput.value = choice.speed;
      speedInput.disabled = !choice.adjustable;
      speedValue.textContent = speedKmh.toFixed(3).replace(/\.?0+$/, "") || speedKmh.toFixed(1);
      selectedLabel.textContent = `Selected: ${choice.name} · ${choice.adjustable ? `${choice.min}–${choice.max} km/h` : `${choice.speed} km/h`}`;
      document.querySelectorAll(".card").forEach(card => {
        card.classList.toggle("active", card.dataset.id === id);
      });
      if (snailMarker) {
        snailMarker.setIcon(makeEmojiIcon(selectedEmoji));
      }
    }

    function makeEmojiIcon(emoji) {
      return L.divIcon({
        className: "snail-icon",
        html: emoji,
        iconSize: [36, 36],
        iconAnchor: [18, 28],
        popupAnchor: [0, -26]
      });
    }

    function buildCharacterGrid() {
      characterGrid.innerHTML = "";
      characters.forEach(({ id, emoji, name, speed, adjustable, min, max }) => {
        const card = document.createElement("button");
        card.type = "button";
        card.className = "card";
        card.dataset.id = id;
        card.innerHTML = `
          <span class="emoji">${emoji}</span>
          <div class="name">${name}</div>
          <div class="speed">${adjustable ? `${min}–${max} km/h (you choose)` : `${speed} km/h`}</div>
        `;
        card.addEventListener("click", () => setCharacter(id));
        characterGrid.appendChild(card);
      });
      setCharacter(selectedCharId);
    }

    function currentSpeedMps() {
      return speedKmh / 3.6;
    }

    function randomOffsetPoint(lat, lng, distanceMeters) {
      // Generates a random point at a fixed distance using great-circle math.
      const R = 6371000; // Earth radius in meters
      const bearing = Math.random() * 2 * Math.PI;
      const delta = distanceMeters / R;
      const φ1 = lat * (Math.PI / 180);
      const λ1 = lng * (Math.PI / 180);

      const φ2 = Math.asin(Math.sin(φ1) * Math.cos(delta) + Math.cos(φ1) * Math.sin(delta) * Math.cos(bearing));
      const λ2 = λ1 + Math.atan2(
        Math.sin(bearing) * Math.sin(delta) * Math.cos(φ1),
        Math.cos(delta) - Math.sin(φ1) * Math.sin(φ2)
      );

      const newLat = φ2 * (180 / Math.PI);
      const newLng = ((λ2 * (180 / Math.PI) + 540) % 360) - 180; // wrap to [-180,180]
      return [newLat, newLng];
    }

    function distanceMeters(a, b) {
      const toRad = d => d * (Math.PI / 180);
      const R = 6371000;
      const dLat = toRad(b[0] - a[0]);
      const dLng = toRad(b[1] - a[1]);
      const lat1 = toRad(a[0]);
      const lat2 = toRad(b[0]);
      const h = Math.sin(dLat / 2) ** 2 + Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLng / 2) ** 2;
      return 2 * R * Math.asin(Math.min(1, Math.sqrt(h)));
    }

    function moveTowards(start, target, maxStepMeters) {
      const dist = distanceMeters(start, target);
      if (dist <= maxStepMeters || dist === 0) return target;
      const ratio = maxStepMeters / dist;
      const lat = start[0] + (target[0] - start[0]) * ratio;
      const lng = start[1] + (target[1] - start[1]) * ratio;
      return [lat, lng];
    }

    function onLocationSuccess(position) {
      const { latitude, longitude, accuracy } = position.coords;
      userCoords = [latitude, longitude];

      if (!userMarker) {
        userMarker = L.marker(userCoords, { icon: markerIcon })
          .addTo(map)
          .bindPopup("You are here")
          .openPopup();
      } else {
        userMarker.setLatLng(userCoords);
      }

      if (accuracy) {
        if (accuracyCircle) {
          accuracyCircle.setLatLng(userCoords).setRadius(accuracy);
        } else {
          accuracyCircle = L.circle(userCoords, { radius: accuracy, color: "#22c55e", weight: 2, fillOpacity: 0.08 }).addTo(map);
        }
      }

      if (gameStarted && !snailCoords) {
        placeSnailRandom();
      }
    }

    function onLocationError(err) {
      setStatus("Unable to fetch location", "Error");
      updateMessage(err.message || "Location access denied. Please enable permission and refresh.");
    }

    function placeSnailRandom() {
      if (!userCoords) {
        updateMessage("Waiting for your location before placing SNAIL.");
        return;
      }
      snailCoords = randomOffsetPoint(userCoords[0], userCoords[1], 5000);
      if (!snailMarker) {
        snailMarker = L.marker(snailCoords, { icon: makeEmojiIcon(selectedEmoji) }).addTo(map).bindPopup("SNAIL (moving)");
      } else {
        snailMarker.setLatLng(snailCoords).setIcon(makeEmojiIcon(selectedEmoji)).bindPopup("SNAIL (moving)");
      }
      map.fitBounds(L.latLngBounds([userCoords, snailCoords]), { padding: [40, 40] });
    }

      if (!navigator.geolocation) {
        setStatus("Geolocation not supported", "Error");
        updateMessage("This browser does not support geolocation.");
      } else {
        setStatus("Requesting location…", "Pending");
      const tickMs = 1000;

      function tick() {
        if (!gameStarted) {
          return setTimeout(tick, tickMs);
        }
        // Wait until we have both points
        if (!userCoords || !snailCoords || !snailMarker) {
          return setTimeout(tick, tickMs);
        }
        const next = moveTowards(snailCoords, userCoords, currentSpeedMps() * (tickMs / 1000));
        snailCoords = next;
        snailMarker.setLatLng(next);
        const dist = distanceMeters(next, userCoords);
        const status = dist > 3 ? "Live" : "Arrived";
        setStatus("Location locked", status);
        updateMessage(
          `You: ${userCoords[0].toFixed(5)} · ${userCoords[1].toFixed(5)} | ` +
          `SNAIL: ${snailCoords[0].toFixed(5)} · ${snailCoords[1].toFixed(5)} · Dist: ${dist.toFixed(1)}m · Speed: ${speedKmh.toFixed(1)} km/h`
        );
        if (status === "Live") {
          setTimeout(tick, tickMs);
        } else {
          snailMarker.bindPopup("SNAIL (arrived)").openPopup();
          userMarker?.openPopup();
        }
      }

      speedInput.addEventListener("input", () => {
        speedKmh = parseFloat(speedInput.value);
        speedValue.textContent = speedKmh.toFixed(1);
      });

      restartBtn.addEventListener("click", () => {
        const ok = window.confirm("Reset the chaser to a new random spot ~5 km away?");
        if (ok) {
          placeSnailRandom();
        }
      });

      openSelectionBtn.addEventListener("click", () => {
        gameStarted = false;
        overlay.classList.remove("hidden");
        setStatus("Selection", "Idle");
        updateMessage("Pick a character to start chasing.");
      });

      startBtn.addEventListener("click", () => {
        gameStarted = true;
        if (!snailCoords) {
          placeSnailRandom();
        }
        overlay.classList.add("hidden");
      });

      buildCharacterGrid();

      navigator.geolocation.watchPosition(
        onLocationSuccess,
        onLocationError,
        { enableHighAccuracy: true, timeout: 12000, maximumAge: 0 }
      );
      tick();
    }
  </script>
</body>
</html>
"""


class InlinePageHandler(SimpleHTTPRequestHandler):
    """Serve a single in-memory HTML page at the root path."""

    def do_GET(self) -> None:  # noqa: N802
        if self.path in ("/", "/index.html"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(HTML_PAGE.encode("utf-8"))))
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode("utf-8"))
        else:
            self.send_error(404, "Not Found")

    def log_message(self, format: str, *args) -> None:
        # Suppress default loud logging; keep it minimal.
        pass


def parse_args() -> Tuple[str, int]:
    parser = argparse.ArgumentParser(description="Serve a local map that shows your current location.")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on (default: 8000)")
    args = parser.parse_args()
    return args.host, args.port


def run_server(host: str, port: int) -> None:
    with HTTPServer((host, port), InlinePageHandler) as httpd:
        print(f"Serving map at http://{host}:{port} — press Ctrl+C to stop.")
        httpd.serve_forever()


def main() -> None:
    host, port = parse_args()
    run_server(host, port)


if __name__ == "__main__":
    main()
