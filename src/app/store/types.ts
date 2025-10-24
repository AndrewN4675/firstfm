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

  // actions
  setUser: (username: string) => void;
  clearUser: () => void;
  setScrobbles: (scrobbles: Scrobble[], fetchedAt?: number) => void;
  clearScrobbleCache: () => void;
};
