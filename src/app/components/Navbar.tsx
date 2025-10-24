"use client";

import Link from "next/link";
import { useState, useEffect } from "react";
import softwareDevelopmentLogo from "../../assets/software-development-logo.png";

const navItems = [
  { label: "Music Map", href: "music-map" },
  { label: "Log in", href: "login" },
];

// Complete functionality of navbar with desktop / mobile views and functionality
export default function Navbar() {
  const [hamburgerOpen, setHamburgerOpen] = useState(false);

  // move to top of screen and prevent scrolling if hamburger is opened
  useEffect(() => {
    if (hamburgerOpen) {
      document.body.style.overflow = "hidden";
      window.scrollTo({ top: 0, behavior: "smooth" });
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [hamburgerOpen]);

  return (
    <>
      <header className="fixed top-0 left-0 w-full z-50 bg-white border-b py-4 px-6 shadow">
        <div className="container mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link href="/" className="flex items-center gap-2 no-underline">
              <span className="font-semibold text-xl">FirstFM</span>
            </Link>
          </div>

          {/* default navigation bar for wider displays */}
          <nav className="hidden md:flex items-center space-x-8">
            {navItems.map(({ label, href }) => (
              <Link key={label} href={href} className="cursor-pointer">
                {label}
              </Link>
            ))}
          </nav>

          {/* hamburger menu on smaller screens */}
          <button
            className="md:hidden p-2"
            onClick={() => setHamburgerOpen(!hamburgerOpen)}
          >
            {!hamburgerOpen ? (
              <>
                {" "}
                {/* hamburger icon */}
                <span className="block w-6 h-0.5 bg-black my-1.25"></span>
                <span className="block w-6 h-0.5 bg-black my-1.25"></span>
                <span className="block w-6 h-0.5 bg-black my-1.25"></span>
              </>
            ) : (
              <div className="relative w-6 h-0.5">
                {" "}
                {/* x icon when open*/}
                <span className="absolute top-0 left-0 w-7 h-0.5 bg-black transform rotate-45"></span>
                <span className="absolute top-0 left-0 w-7 h-0.5 bg-black transform -rotate-45"></span>
              </div>
            )}
          </button>
        </div>
      </header>

      {/* hamburger dropdown to list the navigation items */}
      <div
        className={`absolute top-10 left-0 w-full h-full bg-white/85 backdrop-blur z-40 transition-all duration-250 ease-in-out
        ${
          hamburgerOpen
            ? "opacity-100 translate-y-0"
            : "opacity-0 -translate-y-full"
        }`}
      >
        <div className="w-full py-16 flex flex-col items-center space-y-8 text-xl">
          {navItems.map(({ label, href }) => (
            <Link key={label} href={href} className="cursor-pointer">
              {label}
            </Link>
          ))}
        </div>
      </div>
    </>
  );
}
