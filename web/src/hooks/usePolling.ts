import { useEffect, useRef, useCallback } from "react";

/**
 * 轮询回调 `fetcher`，`intervalMs` 间隔。
 * `enabled` 为 false 时停止轮询。
 */
export function usePolling(
  fetcher: () => void | Promise<void>,
  intervalMs: number,
  enabled: boolean,
) {
  const savedFetcher = useRef(fetcher);
  savedFetcher.current = fetcher;

  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const clear = useCallback(() => {
    if (intervalRef.current !== null) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  useEffect(() => {
    if (!enabled) {
      clear();
      return;
    }
    // 立即执行一次
    savedFetcher.current();
    intervalRef.current = setInterval(() => {
      savedFetcher.current();
    }, intervalMs);
    return clear;
  }, [enabled, intervalMs, clear]);
}
