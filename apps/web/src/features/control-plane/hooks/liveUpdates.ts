import { useEffect } from "react";
import { WS_BASE } from "@/lib/api/httpClient";

export function useLiveInvalidationSocket(invalidateAll: () => void) {
  useEffect(() => {
    if (typeof window === "undefined" || typeof window.WebSocket === "undefined") {
      return;
    }

    let disposed = false;
    let socket: WebSocket | null = null;
    let reconnectHandle: number | undefined;

    const connect = () => {
      if (disposed) {
        return;
      }
      socket = new window.WebSocket(WS_BASE);
      socket.onmessage = (event) => {
        const payload = JSON.parse(event.data) as { type?: string };
        if (payload.type === "system.connected" || payload.type === "system.ping") {
          return;
        }
        invalidateAll();
      };
      socket.onclose = () => {
        if (disposed) {
          return;
        }
        reconnectHandle = window.setTimeout(connect, 1500);
      };
    };

    connect();

    return () => {
      disposed = true;
      if (reconnectHandle) {
        window.clearTimeout(reconnectHandle);
      }
      socket?.close();
    };
  }, [invalidateAll]);
}
