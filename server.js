// Minimal multiplayer chaser server using WebSockets.
// Run with: node server.js

const http = require("http");
const { WebSocketServer } = require("ws");

const PORT = process.env.PORT || 3001;
const TICK_MS = 1000;
const MAX_PLAYERS = 10;
const CATCH_RADIUS_METERS = 3;
const IDLE_TIMEOUT_MS = 1000 * 60 * 30; // 30 minutes
const ADMIN_KEY = "0000";

const rooms = new Map();

function now() {
  return Date.now();
}

function distanceMeters(a, b) {
  const toRad = (d) => (d * Math.PI) / 180;
  const R = 6371000;
  const dLat = toRad(b.lat - a.lat);
  const dLng = toRad(b.lng - a.lng);
  const lat1 = toRad(a.lat);
  const lat2 = toRad(b.lat);
  const h =
    Math.sin(dLat / 2) ** 2 + Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLng / 2) ** 2;
  return 2 * R * Math.asin(Math.min(1, Math.sqrt(h)));
}

function moveTowards(start, target, maxStepMeters) {
  const dist = distanceMeters(start, target);
  if (dist <= maxStepMeters || dist === 0) return { lat: target.lat, lng: target.lng };
  const ratio = maxStepMeters / dist;
  return {
    lat: start.lat + (target.lat - start.lat) * ratio,
    lng: start.lng + (target.lng - start.lng) * ratio,
  };
}

function generateRoomCode() {
  const chars = "ABCDEFGHJKMNPQRSTUVWXYZ23456789";
  let code = "";
  for (let i = 0; i < 6; i++) code += chars[Math.floor(Math.random() * chars.length)];
  return code;
}

function broadcast(room, payload) {
  const msg = JSON.stringify(payload);
  for (const p of room.players.values()) {
    if (p.ws && p.ws.readyState === p.ws.OPEN) {
      p.ws.send(msg);
    }
  }
}

function roomState(room) {
  return {
    type: "state",
    code: room.code,
    name: room.name,
    running: room.running,
    locked: room.locked,
    startedAt: room.startedAt,
    distanceTraveled: room.distanceTraveled,
    chaser: room.chaser,
    targetId: room.targetId,
    caughtId: room.caughtId || null,
    settings: room.settings,
    players: [...room.players.values()].map((p) => ({
      id: p.id,
      name: p.name,
      emoji: p.emoji,
      lat: p.lat,
      lng: p.lng,
      isHost: p.id === room.hostId,
    })),
  };
}

function createRoom(code, hostPlayer, settings, roomName) {
  const room = {
    code,
    name: roomName || `${hostPlayer.name || "Host"}'s Room`,
    hostId: hostPlayer.id,
    players: new Map([[hostPlayer.id, hostPlayer]]),
    settings,
    chaser: { lat: hostPlayer.lat || 0, lng: hostPlayer.lng || 0 },
    targetId: null,
    caughtId: null,
    running: false,
    locked: false,
    startedAt: null,
    distanceTraveled: 0,
    lastStep: now(),
  };
  rooms.set(code, room);
  return room;
}

function nameExists(room, name) {
  const lower = (name || "").toLowerCase();
  for (const p of room.players.values()) {
    if ((p.name || "").toLowerCase() === lower) return true;
  }
  return false;
}

function tickRoom(room) {
  const nowTs = now();
  if (!room.running) {
    room.lastStep = nowTs;
    return;
  }
  const dtSec = Math.min(10, (nowTs - room.lastStep) / 1000);
  room.lastStep = nowTs;

  // pick nearest target
  let nearest = null;
  let minDist = Infinity;
  for (const p of room.players.values()) {
    if (p.lat == null || p.lng == null) continue;
    const d = distanceMeters(room.chaser, p);
    if (d < minDist) {
      minDist = d;
      nearest = p;
    }
  }
  room.targetId = nearest ? nearest.id : null;
  if (!nearest) return;

  const maxStep = (room.settings.speedKmh / 3.6) * dtSec;
  const nextPos = moveTowards(room.chaser, nearest, maxStep);
  room.distanceTraveled += distanceMeters(room.chaser, nextPos);
  room.chaser = nextPos;

  const newDist = distanceMeters(room.chaser, nearest);
  if (newDist <= CATCH_RADIUS_METERS) {
    room.running = false;
    room.locked = true;
    room.caughtId = nearest.id;
  }
}

function handleMessage(ws, data) {
  let msg;
  try {
    msg = JSON.parse(data);
  } catch {
    return;
  }
  const type = msg.type;
  if (type === "create_room") {
    const code = msg.code || generateRoomCode();
    if (rooms.has(code)) {
      ws.send(JSON.stringify({ type: "error", message: "Room already exists" }));
      return;
    }
    const player = {
      id: ws._id,
      name: msg.name || "You",
      emoji: msg.emoji || "🧌",
      lat: msg.lat ?? null,
      lng: msg.lng ?? null,
      ws,
    };
    const settings = {
      character: msg.settings?.character || "snail",
      speedKmh: msg.settings?.speedKmh || 2,
      spawnRadius: msg.settings?.spawnRadius || 5000,
      randomSpawn: !!msg.settings?.randomSpawn,
    };
    const room = createRoom(code, player, settings, msg.roomName);
    ws.send(JSON.stringify({ type: "room_created", code, playerId: ws._id }));
    broadcast(room, roomState(room));
    return;
  }

  if (type === "join_room") {
    let room = rooms.get(msg.code);
    if (!room && msg.mayhem) {
      const settings = {
        character: "snail",
        speedKmh: 0.048,
        spawnRadius: 5000,
        randomSpawn: false,
      };
      const player = {
        id: ws._id,
        name: msg.name || "Player",
        emoji: msg.emoji || "🧌",
        lat: msg.lat ?? null,
        lng: msg.lng ?? null,
        ws,
      };
      room = createRoom(msg.code, player, settings, "Mayhem");
    }
    if (!room) {
      ws.send(JSON.stringify({ type: "error", message: "Room not found" }));
      return;
    }
    if (room.players.size >= MAX_PLAYERS) {
      ws.send(JSON.stringify({ type: "error", message: "Room full" }));
      return;
    }
    if (nameExists(room, msg.name || "Player")) {
      ws.send(JSON.stringify({ type: "error", message: "Name already used" }));
      return;
    }
    const player = {
      id: ws._id,
      name: msg.name || "Player",
      emoji: msg.emoji || "🧌",
      lat: msg.lat ?? null,
      lng: msg.lng ?? null,
      ws,
    };
    room.players.set(player.id, player);
    ws.send(JSON.stringify({ type: "room_joined", code: room.code, playerId: ws._id }));
    broadcast(room, roomState(room));
    return;
  }

  if (type === "list_rooms") {
    const roomsList = [];
    for (const room of rooms.values()) {
      roomsList.push({
        code: room.code,
        name: room.name,
        players: room.players.size,
        running: room.running,
        locked: room.locked,
      });
    }
    ws.send(JSON.stringify({ type: "rooms", rooms: roomsList }));
    return;
  }

  // Messages below need a valid room
  const room = rooms.get(msg.code);
  if (!room) return;

  if (type === "loc") {
    const p = room.players.get(ws._id);
    if (!p) return;
    p.lat = msg.lat;
    p.lng = msg.lng;
    return;
  }

  if (type === "settings" && (ws._id === room.hostId || msg.adminKey === ADMIN_KEY) && !room.running) {
    room.settings = {
      character: msg.settings?.character || room.settings.character,
      speedKmh: msg.settings?.speedKmh || room.settings.speedKmh,
      spawnRadius: msg.settings?.spawnRadius || room.settings.spawnRadius,
      randomSpawn: !!msg.settings?.randomSpawn,
    };
    broadcast(room, roomState(room));
    return;
  }

  if (type === "start" && (ws._id === room.hostId || msg.adminKey === ADMIN_KEY) && !room.running) {
    room.running = true;
    room.locked = true;
    room.startedAt = now();
    room.caughtId = null;
    room.distanceTraveled = 0;
    room.lastStep = now();
    // spawn chaser near host
    const host = room.players.get(room.hostId);
    room.chaser = { lat: host?.lat ?? 0, lng: host?.lng ?? 0 };
    broadcast(room, roomState(room));
    return;
  }
}

function cleanup(ws) {
  for (const room of rooms.values()) {
    if (room.players.delete(ws._id)) {
      if (room.players.size === 0) {
        rooms.delete(room.code);
      } else {
        broadcast(room, roomState(room));
      }
      break;
    }
  }
}

const server = http.createServer((req, res) => {
  res.writeHead(200, { "Content-Type": "text/plain" });
  res.end("ok");
});
const wss = new WebSocketServer({ server });

let idSeq = 1;
wss.on("connection", (ws) => {
  ws._id = `p${idSeq++}`;
  ws.on("message", (data) => handleMessage(ws, data));
  ws.on("close", () => cleanup(ws));
});

setInterval(() => {
  for (const room of rooms.values()) {
    // prune idle rooms
    const idle = room.startedAt && now() - room.startedAt > IDLE_TIMEOUT_MS;
    if (idle && room.players.size === 0) {
      rooms.delete(room.code);
      continue;
    }
    tickRoom(room);
    broadcast(room, roomState(room));
  }
}, TICK_MS);

server.listen(PORT, () => {
  console.log(`Chaser WS server listening on ${PORT}`);
});
