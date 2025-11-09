'use client';

import { createContext, useContext, useRef } from "react";
import { AuthStore, createAuthStore } from "../stores/auth-store";
import { useStore } from "zustand";

export type AuthStoreApi = ReturnType<typeof createAuthStore>;

export const AuthStoreContext = createContext<AuthStoreApi | undefined>(undefined);

export interface AuthStoreProviderProps {
    children: React.ReactNode;
}

export const AuthStoreProvider = ({
    children,
}: AuthStoreProviderProps) => {
    const storeRef = useRef<AuthStoreApi | null>(null);
    if (storeRef.current === null) {
        storeRef.current = createAuthStore();
    }

    return (
        <AuthStoreContext.Provider value={storeRef.current}>
            {children}
        </AuthStoreContext.Provider>
    );
}

export const useAuthStore = <T,>(
    selector: (store: AuthStore) => T,
): T => {
    const authStoreContext = useContext(AuthStoreContext)

    if (!authStoreContext) {
        throw new Error("useAuthStore must be used within an AuthStoreProvider");
    }

    return useStore(authStoreContext, selector);
}
