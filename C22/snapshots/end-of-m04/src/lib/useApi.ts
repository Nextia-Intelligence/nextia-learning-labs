// Our own small data hook: it loads data in an effect, and it cancels the old request when the
// inputs change or the component goes away (the cleanup). Without the cleanup, a slow old answer
// can arrive after a new one and replace it.
import { useEffect, useState, type DependencyList } from 'react';

export type ApiState<T> =
  | { status: 'loading'; data: null; error: null }
  | { status: 'success'; data: T; error: null }
  | { status: 'error'; data: null; error: Error };

export function useApi<T>(load: (signal: AbortSignal) => Promise<T>, deps: DependencyList): ApiState<T> {
  const [state, setState] = useState<ApiState<T>>({ status: 'loading', data: null, error: null });
  useEffect(() => {
    const controller = new AbortController();
    setState({ status: 'loading', data: null, error: null });
    load(controller.signal).then(
      (data) => {
        if (!controller.signal.aborted) setState({ status: 'success', data, error: null });
      },
      (error: Error) => {
        if (!controller.signal.aborted) setState({ status: 'error', data: null, error });
      },
    );
    return () => controller.abort(); // cleanup: the answer of this request is not wanted any more
    // The caller lists every value that `load` uses in `deps`. A missing value means an old answer.
  }, deps);
  return state;
}
