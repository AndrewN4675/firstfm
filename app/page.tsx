'use client';
import React from "react";
import { logIntoLastFM } from "./services/lastfm_user";

export default function Home() {
  return (
    <div className="font-sans grid grid-rows-[20px_1fr_20px] items-center justify-items-center min-h-screen p-8 pb-20 gap-16 sm:p-20">
      <button onClick={() => logIntoLastFM().catch(console.error)}
       className="px-4 py-2 rounded bg-blue-600 text-white"
      >
        Log into your last.fm account!
      </button>
    </div>
  );
}
