"use client";
import GenreGraph from "./genre-graph";

export default function MusicMap() {
  return (
    <div className="h-full w-full">
      <div className="h-[90vh] w-full border-b border-[#282828]">
        <GenreGraph />
      </div>
    </div>
  );
}
