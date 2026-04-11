import { renderHook } from "@testing-library/react";
import { afterEach, describe, expect, test, vi } from "vitest";
import { useLiveInvalidationSocket } from "./hooks";

type Handler = ((event?: { data: string }) => void) | null;

class FakeSocket {
  static instances: FakeSocket[] = [];
  onmessage: Handler = null;
  onclose: (() => void) | null = null;
  closed = false;

  constructor(_url: string) {
    FakeSocket.instances.push(this);
  }

  close() {
    this.closed = true;
  }
}

describe("useLiveInvalidationSocket", () => {
  afterEach(() => {
    FakeSocket.instances = [];
    vi.unstubAllGlobals();
    vi.useRealTimers();
  });

  test("invalidates on non-system websocket messages", () => {
    vi.stubGlobal("WebSocket", FakeSocket as unknown as typeof WebSocket);
    const invalidateAll = vi.fn();

    const { unmount } = renderHook(() => useLiveInvalidationSocket(invalidateAll));
    const socket = FakeSocket.instances[0];

    socket.onmessage?.({ data: JSON.stringify({ type: "task.updated" }) });
    socket.onmessage?.({ data: JSON.stringify({ type: "system.ping" }) });

    expect(invalidateAll).toHaveBeenCalledTimes(1);

    unmount();
    expect(socket.closed).toBe(true);
  });

  test("reconnects after close", () => {
    vi.useFakeTimers();
    vi.stubGlobal("WebSocket", FakeSocket as unknown as typeof WebSocket);
    const invalidateAll = vi.fn();

    renderHook(() => useLiveInvalidationSocket(invalidateAll));
    expect(FakeSocket.instances).toHaveLength(1);

    FakeSocket.instances[0].onclose?.();
    vi.advanceTimersByTime(1500);

    expect(FakeSocket.instances).toHaveLength(2);
  });
});
