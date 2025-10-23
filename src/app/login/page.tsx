'use client';
import { logIntoLastFM } from "../services/lastfm_user";

export default function LoginPage() {
  return (
    <div className="flex flex-col justify-between h-65 max-w-md mx-auto mt-24 p-6 bg-card/80 border border-border rounded-md">
      <div>
        <h1 className="font-semibold text-lg mb-4 mt-4">Log in with Last.fm</h1>
        <p>FirstFM uses your Last.fm account to recommend songs and personalize your experience.</p>
      </div>
      <div className="flex justify-end">
        <button
          onClick={() => logIntoLastFM().catch(console.error)}
          className="px-4 py-2 bg-primary text-primary-foreground rounded-md"
        >
          Sign in with LastFM
        </button>
      </div>
    </div>
  );
}