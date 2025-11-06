"use client";

import { Input } from "@/components/ui/input";
import { useState, useMemo } from "react";
import { Genre } from "./types";
import { Search } from "lucide-react";

export default function GenreSearch({
  nodeMap,
  onSelect, // function to call when user presses enter / clicks a suggested genre
}: {
  nodeMap: Record<string, Genre>;
  onSelect: (name: string) => void;
}) {
  const [searchTerm, setSearchTerm] = useState("");
  const [focused, setFocused] = useState(false);
  const allGenres = useMemo(() => Object.values(nodeMap), [nodeMap]);

  const suggestions = useMemo(() => {
    if (!searchTerm) return [];

    // return the first 3 results from the record based on a cleaned (alphanum) user input
    return allGenres.filter((g) =>
      g.name.toLowerCase().includes(searchTerm.toLowerCase())).slice(0, 3);
  }, [searchTerm]);

  return (
    <div className="relative w-64">
      <Input
        type="text"
        placeholder="Search for a genre..."
        value={searchTerm}
        onFocus={() => setFocused(true)}
        onChange={(e) => setSearchTerm(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter") {
            onSelect(searchTerm); // attempt a search based on the users input field
            setSearchTerm("");
          }
        }}
      />

      {/* dropdown list of suggested genres based on the users input*/}
      {focused && suggestions.length > 0 && (
        <div className="absolute top-full mt-3 w-full bg-white/80 border rounded-lg overflow-hidden">
          {suggestions.map((g) => (
            <div
              key={g.name}
              onClick={() => {
                onSelect(g.name); // use the selected genre from the suggestions list
                setSearchTerm("");
              }}
              className="px-3 py-1 text-sm hover:bg-gray-100/80 cursor-pointer"
            >
              {g.name}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
