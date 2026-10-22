import { useCallback, useEffect, useRef, useState } from "react";

export type AsyncState<T> = {
  data: T | null;
  loading: boolean;
  error: string | null;
};

/**
 * Minimal data-fetching hook with loading/error states.
 * Refetches when `deps` change.
 */
export function useApi<T>(
  fetcher: () => Promise<T>,
  deps: unknown[] = []
): AsyncState<T> & { refetch: () => void } {
  const [state, setState] = useState<AsyncState<T>>({
    data: null,
    loading: true,
    error: null,
  });
  const mounted = useRef(true);
  const fetcherRef = useRef(fetcher);
  fetcherRef.current = fetcher;

  const run = useCallback(() => {
    setState((s) => ({ ...s, loading: true, error: null }));
    fetcherRef
      .current()
      .then((data) => {
        if (mounted.current) setState({ data, loading: false, error: null });
      })
      .catch((err: Error) => {
        if (mounted.current)
          setState({ data: null, loading: false, error: err.message });
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  useEffect(() => {
    mounted.current = true;
    run();
    return () => {
      mounted.current = false;
    };
  }, [run]);

  return { ...state, refetch: run };
}

/**
 * useAsync: an imperative action hook that returns a
 * run function plus loading/error state.
 */
export function useAsync<T, A extends unknown[]>() {
  const [state, setState] = useState<AsyncState<T>>({
    data: null,
    loading: false,
    error: null,
  });

  const run = useCallback(
    (fn: () => Promise<T>, ...args: A) => {
      setState({ data: null, loading: true, error: null });
      return fn()
        .then((data) => {
          setState({ data, loading: false, error: null });
          return data;
        })
        .catch((err: Error) => {
          const message = err.message || "Something went wrong";
          setState({ data: null, loading: false, error: message });
          throw err;
        });
    },
    []
  );

  return { ...state, run };
}
