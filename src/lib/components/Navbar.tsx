"use client";

import Link from "next/link";
import { useState } from "react";
import { Menu, X } from "lucide-react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "../providers/auth-store-provider";

export default function Navbar() {
  const [open, setOpen] = useState(false);
  const router = useRouter();

  const { username, isAuthenticated, clearUser } = useAuthStore(
    (state) => state,
  )

  // Make Music Map the primary "home" landing page
  const navItems = [
    { href: "/music-map", label: "Home" },
    { href: "/library", label: "Library" },
  ];

  function signOut() {
    clearUser();
    try {
      localStorage.removeItem("lastfm-store");
    } catch (e) {
      // ignore (server-side render or restricted storage)
    }
    router.push("/music-map");
  }

  if (!isAuthenticated) {
    return (
      <header className="w-full bg-card/80 backdrop-blur-sm border-b border-border">
        <div className="w-full px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-3">
              <Link href="/music-map" className="flex items-center gap-2 no-underline">
                <span className="font-semibold text-lg">FirstFM</span>
              </Link>
            </div>

            <div className="flex items-center gap-4">
              <Link href="/login">Log in</Link>
            </div>
          </div>
        </div>
      </header>
    );
  }

  return (
    <header className="w-full bg-card/80 backdrop-blur-sm border-b border-border">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center gap-3">
            <Link href="/music-map" className="flex items-center gap-2 no-underline">
              <span className="font-semibold text-lg">FirstFM</span>
            </Link>
          </div>

          <nav className="hidden md:flex items-center space-x-4">
            {navItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="px-3 py-2 rounded-md text-sm hover:bg-muted/60"
              >
                {item.label}
              </Link>
            ))}
          </nav>

          <div className="flex items-center gap-2">
            <div className="hidden md:flex items-center gap-3">
              <div className="text-sm">{username}</div>
              <button
                onClick={signOut}
                className="px-3 py-1 rounded-md hover:bg-muted/60 text-sm"
              >
                Sign out
              </button>
            </div>

            {/* Mobile menu button */}
            <div className="md:hidden">
              <button
                onClick={() => setOpen((v) => !v)}
                aria-label="Toggle menu"
                className="p-2 rounded-md hover:bg-muted/60"
              >
                {open ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Mobile panel */}
      {open && (
        <div className="md:hidden border-t border-border bg-card/95">
          <div className="px-4 pt-2 pb-4 space-y-1">
            {navItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setOpen(false)}
                className="block px-3 py-2 rounded-md text-base hover:bg-muted/60"
              >
                {item.label}
              </Link>
            ))}
            <div className="flex items-center gap-2 px-3 py-2">
              <button
                onClick={() => {
                  setOpen(false);
                  signOut();
                }}
                className="w-full text-left px-3 py-2 rounded-md hover:bg-muted/60"
              >
                Sign out
              </button>
            </div>
          </div>
        </div>
      )}
    </header>
  );
}
