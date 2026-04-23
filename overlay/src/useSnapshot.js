import { useEffect, useState, useRef } from 'react';

const WS_URL = 'ws://127.0.0.1:8765';
const RECONNECT_DELAY_MS = 1000;

export function useSnapshot() {
  const [state, setState] = useState({
    connected: false,
    drivers: [],
    playerIdx: -1,
  });
  const driversMapRef = useRef(new Map());

  useEffect(() => {
    let ws;
    let reconnectTimer;
    let closed = false;

    function applyFull(data) {
      const map = new Map();
      for (const d of data.drivers) map.set(d.idx, d);
      driversMapRef.current = map;
      setState({
        connected: true,
        drivers: [...map.values()].sort((a, b) => a.pos - b.pos),
        playerIdx: data.playerIdx,
      });
    }

    function applyDiff(data) {
      const map = driversMapRef.current;
      for (const d of data.drivers || []) map.set(d.idx, d);
      for (const idx of data.removed || []) map.delete(idx);
      setState(prev => ({
        connected: true,
        drivers: [...map.values()].sort((a, b) => a.pos - b.pos),
        playerIdx: data.playerIdx ?? prev.playerIdx,
      }));
    }

    function connect() {
      try {
        ws = new WebSocket(WS_URL);
      } catch (err) {
        scheduleReconnect();
        return;
      }

      ws.onopen = () => {
        setState(s => ({ ...s, connected: true }));
      };

      ws.onmessage = (event) => {
        let msg;
        try { msg = JSON.parse(event.data); } catch { return; }
        if (msg.type === 'full') applyFull(msg.data);
        else if (msg.type === 'diff') applyDiff(msg.data);
        else if (msg.type === 'inactive') {
          driversMapRef.current = new Map();
          setState({ connected: true, drivers: [], playerIdx: -1 });
        }
      };

      ws.onclose = () => {
        setState(s => ({ ...s, connected: false }));
        scheduleReconnect();
      };

      ws.onerror = () => { /* handled by onclose */ };
    }

    function scheduleReconnect() {
      if (closed) return;
      clearTimeout(reconnectTimer);
      reconnectTimer = setTimeout(connect, RECONNECT_DELAY_MS);
    }

    connect();

    return () => {
      closed = true;
      clearTimeout(reconnectTimer);
      if (ws && ws.readyState === WebSocket.OPEN) ws.close();
    };
  }, []);

  return state;
}
