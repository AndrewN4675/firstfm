"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { fetchUserInfo, Username } from "../../services/lastfm_user";
import { useAuthStore } from "@/src/lib/providers/auth-store-provider";

export default function LastFmCallback() {
  const router = useRouter();
  const { setUser, setScrobbles } = useAuthStore(
    (state) => state,
  )

  useEffect(() => {
    let mounted = true;

    const handleCallback = async () => {
      try {
        const data = await fetchUserInfo();

        if (!mounted) return;

        if (data?.username) {
          setUser(data.username);
          // TODO: optionally fetch recent scrobbles from backend and call setScrobbles(scrobbles)
          router.push("/music-map");
        } else {
          router.replace("/login");
        }
      } catch (err: unknown) {
        console.error("Last.fm callback: failed to fetch user info", err);
        if (mounted) {
          router.replace("/login");
        }
      }
    };

    handleCallback();

    return () => {
      mounted = false;
    };
  }, [setUser, setScrobbles, router]);

  return (
    <div className="p-6 max-w-md mx-auto mt-24">
      <h2 className="text-lg font-medium mb-2">Signing you in…</h2>
      <p>
        If you are not redirected automatically, please return to the app and
        try signing in again.
      </p>
    </div>
  );
}
