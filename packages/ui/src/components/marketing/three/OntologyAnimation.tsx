'use client';

import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import { Float, Sphere, Line } from '@react-three/drei';
import * as THREE from 'three';

interface NodeData {
  position: [number, number, number];
  color: string;
  label: string;
}

const nodes: NodeData[] = [
  { position: [0, 0, 0], color: '#8b5cf6', label: 'Ontology' },
  { position: [1.5, 1, 0.5], color: '#a78bfa', label: 'Customer' },
  { position: [-1.5, 1, -0.5], color: '#a78bfa', label: 'Order' },
  { position: [1.5, -1, -0.5], color: '#a78bfa', label: 'Product' },
  { position: [-1.5, -1, 0.5], color: '#a78bfa', label: 'Invoice' },
  { position: [0, 1.8, 0], color: '#c4b5fd', label: 'Schema' },
];

const edges: [number, number][] = [
  [0, 1], [0, 2], [0, 3], [0, 4], [0, 5],
  [1, 2], [2, 3], [3, 4], [4, 1], [1, 5], [2, 5],
];

function GraphNode({ position, color }: { position: [number, number, number]; color: string }) {
  const ref = useRef<THREE.Mesh>(null);

  useFrame((state) => {
    if (ref.current) {
      ref.current.scale.setScalar(1 + Math.sin(state.clock.elapsedTime * 2) * 0.05);
    }
  });

  return (
    <Float speed={2} rotationIntensity={0.2} floatIntensity={0.3}>
      <Sphere ref={ref} args={[0.15, 32, 32]} position={position}>
        <meshStandardMaterial
          color={color}
          emissive={color}
          emissiveIntensity={0.5}
          roughness={0.3}
          metalness={0.8}
        />
      </Sphere>
    </Float>
  );
}

function GraphEdge({ start, end }: { start: [number, number, number]; end: [number, number, number] }) {
  const points = useMemo(() => [new THREE.Vector3(...start), new THREE.Vector3(...end)], [start, end]);

  return (
    <Line
      points={points}
      color="#8b5cf6"
      lineWidth={1}
      opacity={0.4}
      transparent
    />
  );
}

export function OntologyAnimation() {
  const groupRef = useRef<THREE.Group>(null);

  useFrame((state) => {
    if (groupRef.current) {
      groupRef.current.rotation.y = state.clock.elapsedTime * 0.1;
    }
  });

  return (
    <group ref={groupRef}>
      {nodes.map((node, i) => (
        <GraphNode key={i} position={node.position} color={node.color} />
      ))}
      {edges.map(([startIdx, endIdx], i) => (
        <GraphEdge
          key={i}
          start={nodes[startIdx].position}
          end={nodes[endIdx].position}
        />
      ))}
    </group>
  );
}
