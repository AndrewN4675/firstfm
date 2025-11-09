"use client";
import GenreGraph from "./genre-graph";

export default function MusicMap() {
  return (
    <div className="h-screen w-full flex flex-col">
      <div className="flex-1 w-full">
        <GenreGraph />
      </div>
    </div>
  );
}
