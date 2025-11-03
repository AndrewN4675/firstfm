import { createStore, StateCreator } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

export type Scrobble = {
    id: string;
    artist: string;
    track: string;
    when: string;
};

export type AuthState = {
    username?: string;
    isAuthenticated: boolean;
    lastFetchedAt?: number;
    scrobbleCache: Scrobble[];
};

export type AuthActions = {
    setUser: (username: string) => void;
    clearUser: () => void;
    setScrobbles: (scrobbles: Scrobble[], fetchedAt?: number) => void;
    clearScrobbleCache: () => void;
};

export type AuthStore = AuthState & AuthActions;

export const defaultInitState: AuthState = {
    username: undefined,
    isAuthenticated: false,
    lastFetchedAt: undefined,
    scrobbleCache: [],
};

export const createAuthStore = (
    initState: AuthState = defaultInitState
) => {
    return createStore<AuthStore>(
        (persist(
            (set) => ({
                ...initState,
                setUser: (username: string) => set(() => ({ username, isAuthenticated: true })),
                clearUser: () =>
                    set(() => ({ username: undefined, isAuthenticated: false })),
                setScrobbles: (scrobbles: Scrobble[], fetchedAt: number = Date.now()) =>
                    set(() => ({
                        scrobbleCache: scrobbles.slice(0, 200),
                        lastFetchedAt: fetchedAt,
                    })),
                clearScrobbleCache: () =>
                    set(() => ({ scrobbleCache: [], lastFetchedAt: undefined })),
            }),
            {
                name: "lastfm-store",
                // Use localStorage for persistence. This file is only executed
                // client-side because the provider creates the store inside a
                // client component, so this is safe.
                storage: createJSONStorage(() => localStorage as Storage),
                // Only persist the plain state (not the action functions)
                partialize: (state: AuthState) => ({
                    username: state.username,
                    isAuthenticated: state.isAuthenticated,
                    lastFetchedAt: state.lastFetchedAt,
                    scrobbleCache: state.scrobbleCache,
                }),
            }
        ) as unknown as StateCreator<AuthStore>)
    );
}