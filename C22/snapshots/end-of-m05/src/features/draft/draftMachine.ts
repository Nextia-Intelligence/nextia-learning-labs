// The states of one AI draft, and the only ways to move between them. One function (a reducer)
// decides every change, so the screen can never show two states at once.
//
//   idle → connecting → streaming → done
//                    ↘            ↘ stopped      (the agent pressed Stop)
//                     failed       ↘ interrupted (the connection ended before the end)
//                                  ↘ failed      (the server sent an error)
//                                  ↘ invalid     (the final draft did not pass the checks)
import type { Draft } from '../../api/drafts';

export type DraftStatus = 'idle' | 'connecting' | 'streaming' | 'done' | 'stopped' | 'interrupted' | 'failed' | 'invalid';

export interface DraftState {
  status: DraftStatus;
  text: string;
  pieces: number;
  draft: Draft | null;
  problem: string | null;
}

export type DraftAction =
  | { type: 'start' }
  | { type: 'token'; text: string }
  | { type: 'done'; draft: Draft }
  | { type: 'invalid'; problem: string }
  | { type: 'stop' }
  | { type: 'ended' }
  | { type: 'fail'; problem: string }
  | { type: 'reset' };

export const initialDraft: DraftState = { status: 'idle', text: '', pieces: 0, draft: null, problem: null };

const active = (s: DraftStatus) => s === 'connecting' || s === 'streaming';

export function draftReducer(state: DraftState, action: DraftAction): DraftState {
  switch (action.type) {
    case 'start':
      return active(state.status) ? state : { ...initialDraft, status: 'connecting' };
    case 'token':
      return active(state.status)
        ? { ...state, status: 'streaming', text: state.text + action.text, pieces: state.pieces + 1 }
        : state;
    case 'done':
      return active(state.status) ? { ...state, status: 'done', draft: action.draft } : state;
    case 'invalid':
      return active(state.status) ? { ...state, status: 'invalid', problem: action.problem } : state;
    case 'stop':
      return active(state.status) ? { ...state, status: 'stopped' } : state;
    case 'ended':
      return active(state.status) ? { ...state, status: 'interrupted' } : state;
    case 'fail':
      return active(state.status) ? { ...state, status: 'failed', problem: action.problem } : state;
    case 'reset':
      return initialDraft;
  }
}
