'use client';

import Link from "next/link";
import { useState } from "react";
import { Menu, X, Music } from "lucide-react";

export default function Navbar() {
  const [open, setOpen] = useState(false);
  const user = false; // Placeholder for user authentication state

  const navItems = [
    { href: "/", label: "Home" },
    { href: "/library", label: "Library" },
  ];

  if (!user) {
    return (
      <header className="w-full bg-card/80 backdrop-blur-sm border-b border-border">
        <div className="w-full px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-3">
              <Link href="/" className="flex items-center gap-2 no-underline">
                <span className="font-semibold text-lg">FirstFM</span>
              </Link>
            </div>

            <div className="flex items-center gap-4">
              <Link
                href="/login"
              >
                Log in
              </Link>
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
            <Link href="/" className="flex items-center gap-2 no-underline">
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
            <div className="hidden md:block">
              <button
                type="button"
                aria-label="Profile"
                className="w-9 h-9 rounded-full bg-muted/40 flex items-center justify-center text-sm font-medium"
                // title={} placeholder for user name
                onClick={() => {
                  // Implement profile click functionality
                }}
              >
                {/* Placeholder for user initial */}
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
                onClick={() => {}} // Implement logout functionality
                className="w-full text-left px-3 py-2 rounded-md hover:bg-muted/60"
              >
                Log out
              </button>
            </div>
          </div>
        </div>
      )}
    </header>
  );
}
