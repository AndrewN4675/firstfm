"use client";

import * as THREE from "three";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { OrbitControls, Text } from "@react-three/drei";
import { useEffect, useState, useMemo, useRef } from "react";
import { Button } from "@/components/ui/button";
import Papa from "papaparse";
import { Genre } from "./types";
import GenreSearch from "./genre-search";

// circle geometries, created once and reused for all nodes
const radius = 0.8;
const circleGeo = new THREE.CircleGeometry(radius, 32);

function CameraController({ targetGenre }: { targetGenre: Genre | null }) {
  const { camera } = useThree();
  const controlsRef = useRef<any>(null);

  useFrame(() => {
    if (targetGenre && controlsRef.current) {
      // Calculate target position (move camera back from the node)
      const targetPos = new THREE.Vector3(
        targetGenre.x,
        targetGenre.y,
        targetGenre.z + 10 // offset camera behind the node
      );

      // Smoothly interpolate camera position
      camera.position.lerp(targetPos, 0.05);

      // Update controls target to focus on the node
      const focusPoint = new THREE.Vector3(
        targetGenre.x,
        targetGenre.y,
        targetGenre.z
      );
      controlsRef.current.target.lerp(focusPoint, 0.05);
      controlsRef.current.update();
    }
  });

  return (
    <OrbitControls
      ref={controlsRef}
      enablePan
      enableZoom
      enableRotate
      maxDistance={1000}
      minDistance={0}
    />
  );
}

function GenreNode({ genre }: { genre: Genre }) {
  const [hovered, setHovered] = useState(false);
  const meshReference = useRef<THREE.Mesh>(null);
  const textReference = useRef<any>(null);
  const { camera } = useThree();

  const position = useMemo(
    () => [genre.x, genre.y, genre.z] as [number, number, number],
    [genre.x, genre.y, genre.z]
  );

  useFrame(() => {
    if (meshReference.current) {
      meshReference.current.lookAt(camera.position);
      const smoothingFactor = 0.2;

      // smoothly increase hovered nodes size
      const targetScale = hovered ? 1.5 : 1.0;
      meshReference.current.scale.lerp(
        new THREE.Vector3(targetScale, targetScale, targetScale),
        smoothingFactor
      );
    }
    // always ensure that genre name text always faces the camera
    if (textReference.current) {
      textReference.current.lookAt(camera.position);
    }
  });

  return (
    <group position={position}>
      <mesh
        ref={meshReference}
        geometry={circleGeo} // use same geometry for every node
        onPointerOver={(e) => {
          // highlight nodes in cursors path
          e.stopPropagation(); // stop at=the first node hit (removes highlighting nodes behind one another)
          setHovered(true);
        }}
        onPointerOut={(e) => {
          // revert once not hovering anymore
          e.stopPropagation();
          setHovered(false);
        }}
        onPointerDown={(e) => e.stopPropagation()}
      >
        <meshBasicMaterial
          attach="material"
          color={hovered ? "#db3822" : "#4b4b4b"} // red when hovered, grey otherwise
          transparent
          opacity={0.9}
        />
      </mesh>
      // visible genre name on hover only
      {hovered && (
        <Text
          ref={textReference}
          position={[0, 3, 0]}
          fontSize={2}
          color="#101010"
          anchorX="center"
          anchorY="middle"
        >
          {genre.name}
        </Text>
      )}
    </group>
  );
}

function Connections({
  nodes,
  threshold = 1,
}: {
  nodes: Record<string, Genre>;
  threshold?: number;
}) {
  const geometry = useMemo(() => {
    const posArray: number[] = [];
    const vals = Object.values(nodes);

    for (let i = 0; i < vals.length; i++) {
      for (let j = i + 1; j < vals.length; j++) {
        const dx = vals[i].x - vals[j].x;
        const dy = vals[i].y - vals[j].y;
        const dz = vals[i].z - vals[j].z;
        const dist = Math.sqrt(dx * dx + dy * dy + dz * dz);

        if (dist <= threshold) {
          posArray.push(vals[i].x, vals[i].y, vals[i].z);
          posArray.push(vals[j].x, vals[j].y, vals[j].z);
        }
      }
    }

    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.Float32BufferAttribute(posArray, 3));
    return geo;
  }, [nodes, threshold]);

  return (
    <lineSegments geometry={geometry}>
      <lineBasicMaterial color="#101010" opacity={0.2} transparent />
    </lineSegments>
  );
}

export default function GenreGraph() {
  const [nodeMap, setNodeMap] = useState<Record<string, Genre>>({}); // record (hash table) for faster indexing for search
  const [targetGenre, setTargetGenre] = useState<Genre | null>(null);

  useEffect(() => {
    Papa.parse("genre_coords.csv", {
      download: true,
      header: true,
      skipEmptyLines: true,
      complete: (results) => {
        const parsed = results.data as any[];

        const map: Record<string, Genre> = {}; // temp record
        for (const line of parsed) {
          const name = line.name;
          const x = Number(line.x);
          const y = Number(line.y);
          const z = Number(line.z);
          const hex = line.hex ?? "";

          if (!name || Number.isNaN(x) || Number.isNaN(y) || Number.isNaN(z)) {
            continue;
          }

          const genre: Genre = {
            name: String(name),
            hex: String(hex),
            x,
            y,
            z,
          };

          map[genre.name] = genre; // insert genre into record with its name being the key
        }

        setNodeMap(map); // set react state for the newly filled record
      },
    });
  }, []);

  // Memoize the rendered nodes
  const renderedNodes = useMemo(() => {
    return Object.values(nodeMap).map((node, i) => (
      <GenreNode key={i} genre={node} />
    ));
  }, [nodeMap]);

  return (
    <div className="w-full h-full bg-white relative">
      {/* overlay for the search bar and random seek button */}
      <div className="absolute top-4 right-4 flex gap-2 z-10 bg-white/80 p-2 rounded-lg shadow">
        {/* TODO: placeholder onSelect for now, will move camera to node */}
        <GenreSearch
          nodeMap={nodeMap}
          onSelect={(name: string) => {
            const genre = nodeMap[name];
            if (genre) {
              setTargetGenre(genre);
              setTimeout(() => setTargetGenre(null), 5000);
            }
          }}
        />
        <Button variant="outline">Random</Button>
      </div>

      {/* 3d interactive graph */}
      <Canvas
        camera={{
          position: [0, 0, 400],
          near: 0.1,
          far: 5000,
          fov: 75,
        }}
        gl={{
          antialias: false,
          powerPreference: "high-performance",
        }}
      >
        {/* render stuff */}
        <ambientLight intensity={0.6} />
        <Connections nodes={nodeMap} threshold={20} />
        {renderedNodes}

        <CameraController targetGenre={targetGenre} />

        <Text visible={false}>
          dummy text to load font shader to fix flashing
        </Text>
      </Canvas>
    </div>
  );
}
