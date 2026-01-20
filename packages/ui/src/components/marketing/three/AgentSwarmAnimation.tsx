'use client';

import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import { Sphere, Trail } from '@react-three/drei';
import * as THREE from 'three';

const clusterColors = [
  '#8b5cf6', // violet - Discovery
  '#a78bfa', // light violet - Data Architect
  '#7c3aed', // purple - App Builder
  '#06b6d4', // cyan - Operations
  '#c4b5fd', // lavender - Enablement
  '#6366f1', // indigo - Orchestration
];

function Agent({
  clusterIndex,
  agentIndex,
  totalInCluster
}: {
  clusterIndex: number;
  agentIndex: number;
  totalInCluster: number;
}) {
  const ref = useRef<THREE.Mesh>(null);
  const color = clusterColors[clusterIndex % clusterColors.length];

  const initialAngle = (agentIndex / totalInCluster) * Math.PI * 2;
  const clusterAngle = (clusterIndex / 6) * Math.PI * 2;
  const clusterRadius = 1.2;
  const orbitRadius = 0.3 + (agentIndex % 3) * 0.15;

  useFrame((state) => {
    if (ref.current) {
      const time = state.clock.elapsedTime;
      const speed = 0.5 + (agentIndex % 3) * 0.2;

      const cx = Math.cos(clusterAngle + time * 0.1) * clusterRadius;
      const cy = Math.sin(time * 0.2 + clusterIndex) * 0.3;
      const cz = Math.sin(clusterAngle + time * 0.1) * clusterRadius;

      const ax = Math.cos(initialAngle + time * speed) * orbitRadius;
      const ay = Math.sin(time * speed * 0.5) * 0.1;
      const az = Math.sin(initialAngle + time * speed) * orbitRadius;

      ref.current.position.set(cx + ax, cy + ay, cz + az);

      const pulse = 1 + Math.sin(time * 3 + agentIndex) * 0.1;
      ref.current.scale.setScalar(pulse);
    }
  });

  return (
    <Trail width={0.5} length={4} color={color} attenuation={(t) => t * t}>
      <Sphere ref={ref} args={[0.05, 16, 16]}>
        <meshStandardMaterial
          color={color}
          emissive={color}
          emissiveIntensity={0.8}
          roughness={0.2}
          metalness={0.9}
        />
      </Sphere>
    </Trail>
  );
}

export function AgentSwarmAnimation() {
  const groupRef = useRef<THREE.Group>(null);

  const agents = useMemo(() => {
    const result: { clusterIndex: number; agentIndex: number; total: number }[] = [];
    const agentsPerCluster = [4, 3, 4, 4, 3, 3];

    agentsPerCluster.forEach((count, clusterIdx) => {
      for (let i = 0; i < count; i++) {
        result.push({ clusterIndex: clusterIdx, agentIndex: i, total: count });
      }
    });

    return result;
  }, []);

  useFrame((state) => {
    if (groupRef.current) {
      const scale = 1 + Math.sin(state.clock.elapsedTime * 0.5) * 0.05;
      groupRef.current.scale.setScalar(scale);
    }
  });

  return (
    <group ref={groupRef}>
      {agents.map((agent, i) => (
        <Agent
          key={i}
          clusterIndex={agent.clusterIndex}
          agentIndex={agent.agentIndex}
          totalInCluster={agent.total}
        />
      ))}
    </group>
  );
}
