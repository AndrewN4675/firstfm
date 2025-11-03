import { createStore } from "zustand";

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
    return createStore<AuthStore>((set) => ({
        ...initState,
        setUser: (username) => set(() => ({ username, isAuthenticated: true })),
        clearUser: () =>
            set(() => ({ username: undefined, isAuthenticated: false })),
        setScrobbles: (scrobbles, fetchedAt = Date.now()) =>
            set(() => ({
                scrobbleCache: scrobbles.slice(0, 200),
                lastFetchedAt: fetchedAt,
            })),
        clearScrobbleCache: () =>
            set(() => ({ scrobbleCache: [], lastFetchedAt: undefined })),
    }));
}