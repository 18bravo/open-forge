'use client';

/**
 * Organization View - 3D DoD organizational structure
 */

import { useRef, useState, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Html, Line } from '@react-three/drei';
import * as THREE from 'three';
import { ORG_NODES, ORG_CONNECTIONS } from '../data';
import type { OrgNode } from '../types';

interface OrganizationViewProps {
  selectedId: string | null;
  onSelect: (id: string) => void;
}

export function OrganizationView({ selectedId, onSelect }: OrganizationViewProps) {
  return (
    <div className="w-full h-full">
      <Canvas camera={{ position: [0, 2, 10], fov: 50 }}>
        <ambientLight intensity={0.4} />
        <pointLight position={[10, 10, 10]} intensity={1} />
        <pointLight position={[-10, -5, -10]} intensity={0.3} color="#8b5cf6" />

        {/* Connections */}
        {ORG_CONNECTIONS.map(conn => (
          <OrgConnection key={conn.id} connection={conn} />
        ))}

        {/* Nodes */}
        {ORG_NODES.map(node => (
          <OrgNodeMesh
            key={node.id}
            node={node}
            isSelected={selectedId === node.id}
            onSelect={onSelect}
          />
        ))}

        <OrbitControls
          enablePan
          minDistance={5}
          maxDistance={20}
          autoRotate
          autoRotateSpeed={0.2}
        />

        {/* Grid floor */}
        <gridHelper args={[20, 20, '#334155', '#1e293b']} position={[0, -4, 0]} />
      </Canvas>

      {/* Level Legend */}
      <div className="absolute bottom-6 left-6 bg-slate-900/90 backdrop-blur-xl rounded-lg border border-slate-700/50 p-4">
        <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
          Organization Levels
        </h3>
        <div className="space-y-2">
          <LevelItem color="#fbbf24" label="Department" level={0} />
          <LevelItem color="#8b5cf6" label="Major Components" level={1} />
          <LevelItem color="#84cc16" label="Commands & Agencies" level={2} />
        </div>
      </div>
    </div>
  );
}

function LevelItem({ color, label, level }: { color: string; label: string; level: number }) {
  return (
    <div className="flex items-center gap-2">
      <div
        className="w-3 h-3 rounded"
        style={{ backgroundColor: color }}
      />
      <span className="text-sm text-slate-300">{label}</span>
      <span className="text-xs text-slate-500">(L{level})</span>
    </div>
  );
}

interface OrgNodeMeshProps {
  node: OrgNode;
  isSelected: boolean;
  onSelect: (id: string) => void;
}

function OrgNodeMesh({ node, isSelected, onSelect }: OrgNodeMeshProps) {
  const [hovered, setHovered] = useState(false);
  const meshRef = useRef<THREE.Mesh>(null);
  const glowRef = useRef<THREE.Mesh>(null);

  useFrame((state, delta) => {
    if (meshRef.current) {
      // Gentle float animation
      meshRef.current.position.y = node.position[1] + Math.sin(state.clock.elapsedTime + node.position[0]) * 0.05;

      // Scale on hover/select
      const targetScale = (hovered || isSelected) ? node.size * 1.2 : node.size;
      meshRef.current.scale.lerp(
        new THREE.Vector3(targetScale, targetScale, targetScale),
        delta * 5
      );
    }

    if (glowRef.current) {
      const pulse = 1 + Math.sin(state.clock.elapsedTime * 2) * 0.1;
      glowRef.current.scale.set(pulse, pulse, pulse);
    }
  });

  const geometry = useMemo(() => {
    switch (node.type) {
      case 'department':
        return <octahedronGeometry args={[1, 0]} />;
      case 'component':
        return <boxGeometry args={[1, 1, 1]} />;
      case 'command':
        return <dodecahedronGeometry args={[1, 0]} />;
      case 'agency':
        return <icosahedronGeometry args={[1, 0]} />;
      default:
        return <sphereGeometry args={[1, 16, 16]} />;
    }
  }, [node.type]);

  return (
    <group position={node.position as [number, number, number]}>
      {/* Main node */}
      <mesh
        ref={meshRef}
        onClick={() => onSelect(node.id)}
        onPointerOver={() => setHovered(true)}
        onPointerOut={() => setHovered(false)}
      >
        {geometry}
        <meshStandardMaterial
          color={node.color}
          emissive={node.color}
          emissiveIntensity={isSelected ? 0.6 : hovered ? 0.4 : 0.2}
          metalness={0.3}
          roughness={0.7}
        />
      </mesh>

      {/* Glow effect for selected */}
      {isSelected && (
        <mesh ref={glowRef} scale={node.size * 1.5}>
          <sphereGeometry args={[1, 16, 16]} />
          <meshBasicMaterial
            color={node.color}
            transparent
            opacity={0.15}
          />
        </mesh>
      )}

      {/* Label */}
      <Html
        position={[0, node.size + 0.3, 0]}
        center
        style={{ pointerEvents: 'none' }}
      >
        <div
          className={`
            px-2 py-1 rounded backdrop-blur transition-opacity
            ${hovered || isSelected ? 'bg-slate-900/95 opacity-100' : 'bg-slate-900/70 opacity-70'}
          `}
        >
          <p className="text-xs font-semibold text-white whitespace-nowrap">{node.abbrev}</p>
          {(hovered || isSelected) && (
            <p className="text-xs text-slate-400 whitespace-nowrap max-w-[150px] truncate">
              {node.name}
            </p>
          )}
        </div>
      </Html>
    </group>
  );
}

interface ConnectionProps {
  connection: {
    id: string;
    sourceId: string;
    targetId: string;
    color: string;
  };
}

function OrgConnection({ connection }: ConnectionProps) {
  const sourceNode = ORG_NODES.find(n => n.id === connection.sourceId);
  const targetNode = ORG_NODES.find(n => n.id === connection.targetId);

  if (!sourceNode || !targetNode) return null;

  const points = useMemo(() => {
    const start = new THREE.Vector3(...sourceNode.position);
    const end = new THREE.Vector3(...targetNode.position);
    const mid = new THREE.Vector3().lerpVectors(start, end, 0.5);
    mid.y += 0.5; // Arc upward

    const curve = new THREE.QuadraticBezierCurve3(start, mid, end);
    return curve.getPoints(20);
  }, [sourceNode.position, targetNode.position]);

  return (
    <Line
      points={points}
      color={connection.color}
      lineWidth={1}
      transparent
      opacity={0.4}
    />
  );
}
