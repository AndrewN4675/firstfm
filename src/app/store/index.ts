import { devtools, persist, createJSONStorage } from "zustand/middleware";
import { createAuthSlice } from "./slices/auth";
import { create } from "zustand";
import { AuthState } from "./types";

type StoreState = AuthState;

export const useStore = create<StoreState>()(
  devtools(
    persist(
      (set, get, store) => ({
        ...createAuthSlice(set, get, store),
      }),
      {
        name: "lastfm-store",
        partialize: (state) => ({
          username: state.username,
          isAuthenticated: state.isAuthenticated,
          scrobbleCache: state.scrobbleCache,
          lastFetchedAt: state.lastFetchedAt,
        }),
        storage: createJSONStorage(() => localStorage),
      }
    )
  )
);
