'use client';

import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { OrbitControls, Text } from '@react-three/drei';
import Papa from 'papaparse';
import { useEffect, useState, useMemo, useRef } from 'react';
import * as THREE from 'three';

interface Genre {
    name: string;
    hash: string;
    hex: string;
    x: number;
    y: number;
    z: number;
}

// circle geometries, created once and reused for all nodes
const radius = 0.8;
const circleGeo = new THREE.CircleGeometry(radius, 32);

function GenreNode({ genre }: { genre: Genre }) {
    const [hovered, setHovered] = useState(false);
    const meshReference = useRef<THREE.Mesh>(null);
    const textReference = useRef<any>(null);
    const { camera } = useThree();

    const position = useMemo(() => 
        [genre.x, genre.y, genre.z] as [number, number, number], 
        [genre.x, genre.y, genre.z]
    );

    useFrame(() => {
        if (meshReference.current) {
            meshReference.current.lookAt(camera.position);
            const smoothingFactor = 0.2;
            // smoothly increase hovered nodes size
            const targetScale = hovered ? 1.5 : 1.0;
            meshReference.current.scale.lerp(new THREE.Vector3(targetScale, targetScale, targetScale), smoothingFactor);
        }
        if (textReference.current) {
            textReference.current.lookAt(camera.position);
        }
    });

    return (
        <group position={position}>
            <mesh
                ref={meshReference}
                geometry={circleGeo} // use same geometry for every node
                onPointerOver={(e) => { // highlight nodes in cursors path
                    e.stopPropagation(); // stop at=the first node hit (removes highlighting nodes behind one another)
                    setHovered(true);
                }}
                onPointerOut={(e) => { // revert once not hovering anymore
                    e.stopPropagation();
                    setHovered(false);
                }}
                onPointerDown={(e) => e.stopPropagation()}
            >
            <meshBasicMaterial
                attach="material"
                color={hovered ? '#db3822' : '#4b4b4b'} // red when hovered, grey otherwise
                transparent
                opacity={0.9}
            />
            </mesh>

    {hovered && (
        <Text
            ref={textReference}
            position={[0, 3, 0]}
            fontSize={2}
            color='#101010'
            anchorX='center'
            anchorY='middle'
        >
            {genre.name}
        </Text>
    )}
    </group>
);
}

function Connections({ nodes, threshold = 1 }: { nodes: Genre[]; threshold?: number }) {
const geometry = useMemo(() => {
    const posArray: number[] = [];

    for (let i = 0; i < nodes.length; i++) {
    for (let j = i + 1; j < nodes.length; j++) {
        const dx = nodes[i].x - nodes[j].x;
        const dy = nodes[i].y - nodes[j].y;
        const dz = nodes[i].z - nodes[j].z;
        const dist = Math.sqrt(dx * dx + dy * dy + dz * dz);

        if (dist <= threshold) {
        posArray.push(nodes[i].x, nodes[i].y, nodes[i].z);
        posArray.push(nodes[j].x, nodes[j].y, nodes[j].z);
        }
    }
    }

    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.Float32BufferAttribute(posArray, 3));
    return geo;
}, [nodes]);

return (
    <lineSegments geometry={geometry}>
    <lineBasicMaterial color='#101010' opacity={0.2} transparent />
    </lineSegments>
);
}

export default function GenreGraph() {
const [nodes, setNodes] = useState<Genre[]>([]);

useEffect(() => {
    Papa.parse('/genre_coords.csv', {
    download: true,
    header: true,
    dynamicTyping: false,
    skipEmptyLines: true,
    complete: (results) => {
        const parsed = results.data as any[];

        const validNodes: Genre[] = parsed
        .map(node => ({
            name: node.name,
            hash: node.hash,
            hex: node.hex,
            x: Number(node.x),
            y: Number(node.y),
            z: Number(node.z),
        }))
        .filter(node => 
            node.name &&
            !isNaN(node.x) &&
            !isNaN(node.y) &&
            !isNaN(node.z)
        );

        setNodes(validNodes);
    },
    });
}, []);

// Memoize the rendered nodes
const renderedNodes = useMemo(() => {
    return nodes.map((node, i) => (
    <GenreNode key={i} genre={node}/>
    ));
}, [nodes]);

return (
    <div className='w-full h-full bg-[#FFFFFF] relative'>
    <Canvas 
        camera={{ 
        position: [0, 0, 400], 
        near: 0.1, 
        far: 5000,
        fov: 75
        }}
        gl={{ 
        antialias: false,
        powerPreference: 'high-performance'
        }}
    >

        // render stuff
        <ambientLight intensity={0.6} />
        <Connections nodes={nodes} threshold={20} />
        {renderedNodes}
        
        <OrbitControls 
        enablePan 
        enableZoom 
        enableRotate 
        maxDistance={1000}
        minDistance={50}
        />
    </Canvas>
    </div>
);
}
