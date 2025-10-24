import { StateCreator } from "zustand";
import { AuthState } from "../types";

export const createAuthSlice: StateCreator<AuthState> = (set, get) => ({
  username: undefined,
  isAuthenticated: false,
  lastFetchedAt: undefined,
  scrobbleCache: [],

  setUser: (username) => set(() => ({ username, isAuthenticated: true })),

  clearUser: () =>
    set(() => ({
      username: undefined,
      isAuthenticated: false,
      scrobbleCache: [],
      lastFetchedAt: undefined,
    })),

  setScrobbles: (scrobbles, fetchedAt = Date.now()) =>
    // limit cache length to avoid huge localStorage writes
    set(() => ({
      scrobbleCache: scrobbles.slice(0, 200),
      lastFetchedAt: fetchedAt,
    })),

  clearScrobbleCache: () =>
    set(() => ({ scrobbleCache: [], lastFetchedAt: undefined })),
});
