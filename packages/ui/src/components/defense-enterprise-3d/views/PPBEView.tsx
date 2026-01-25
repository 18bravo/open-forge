'use client';

/**
 * PPBE View - Interactive process flow visualization
 */

import { useRef, useState } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Html, RoundedBox } from '@react-three/drei';
import * as THREE from 'three';
import { PPBE_PHASES, PPBE_TIMELINE } from '../data';
import type { PPBEPhase } from '../types';

interface PPBEViewProps {
  selectedId: string | null;
  onSelect: (id: string) => void;
}

export function PPBEView({ selectedId, onSelect }: PPBEViewProps) {
  return (
    <div className="w-full h-full">
      <Canvas camera={{ position: [0, 3, 8], fov: 50 }}>
        <ambientLight intensity={0.4} />
        <pointLight position={[10, 10, 10]} intensity={1} />
        <directionalLight position={[-5, 5, 5]} intensity={0.5} />

        {/* Phase blocks */}
        {PPBE_PHASES.map((phase, index) => (
          <PhaseBlock
            key={phase.id}
            phase={phase}
            index={index}
            total={PPBE_PHASES.length}
            isSelected={selectedId === phase.id}
            onSelect={onSelect}
          />
        ))}

        {/* Flow arrows */}
        <FlowArrows />

        {/* Cycle indicator */}
        <CycleRing />

        <OrbitControls
          enablePan
          minDistance={5}
          maxDistance={15}
          autoRotate
          autoRotateSpeed={0.1}
        />
      </Canvas>

      {/* Timeline Legend */}
      <div className="absolute bottom-6 left-6 bg-slate-900/90 backdrop-blur-xl rounded-lg border border-slate-700/50 p-4 max-w-sm">
        <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
          Overlapping Cycles
        </h3>
        <p className="text-xs text-slate-400 mb-3">{PPBE_TIMELINE.description}</p>
        <div className="space-y-2">
          {PPBE_TIMELINE.cycles.map((cycle, i) => (
            <div key={i} className="flex items-center justify-between">
              <span className="text-sm text-slate-300">{cycle.phase}</span>
              <span className="text-xs text-slate-500">{cycle.label}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

interface PhaseBlockProps {
  phase: PPBEPhase;
  index: number;
  total: number;
  isSelected: boolean;
  onSelect: (id: string) => void;
}

function PhaseBlock({ phase, index, total, isSelected, onSelect }: PhaseBlockProps) {
  const [hovered, setHovered] = useState(false);
  const groupRef = useRef<THREE.Group>(null);
  const meshRef = useRef<THREE.Mesh>(null);

  // Position in a circle
  const angle = (index / total) * Math.PI * 2 - Math.PI / 2;
  const radius = 3;
  const x = Math.cos(angle) * radius;
  const z = Math.sin(angle) * radius;

  useFrame((state, delta) => {
    if (groupRef.current) {
      // Float animation
      groupRef.current.position.y = Math.sin(state.clock.elapsedTime + index) * 0.1;
    }

    if (meshRef.current) {
      // Scale on interaction
      const targetScale = (hovered || isSelected) ? 1.1 : 1;
      meshRef.current.scale.lerp(
        new THREE.Vector3(targetScale, targetScale, targetScale),
        delta * 5
      );

      // Rotate to face center
      meshRef.current.lookAt(0, meshRef.current.position.y, 0);
    }
  });

  return (
    <group ref={groupRef} position={[x, 0, z]}>
      <RoundedBox
        ref={meshRef}
        args={[1.5, 2, 0.3]}
        radius={0.1}
        smoothness={4}
        onClick={() => onSelect(phase.id)}
        onPointerOver={() => setHovered(true)}
        onPointerOut={() => setHovered(false)}
      >
        <meshStandardMaterial
          color={phase.color}
          emissive={phase.color}
          emissiveIntensity={isSelected ? 0.5 : hovered ? 0.3 : 0.1}
          metalness={0.2}
          roughness={0.8}
        />
      </RoundedBox>

      {/* Phase indicator circle */}
      <mesh position={[0, 1.3, 0.2]}>
        <circleGeometry args={[0.25, 32]} />
        <meshBasicMaterial color={phase.color} />
      </mesh>

      {/* Phase letter */}
      <Html position={[0, 1.3, 0.3]} center style={{ pointerEvents: 'none' }}>
        <div className="text-white font-bold text-lg">{phase.abbrev}</div>
      </Html>

      {/* Label */}
      <Html position={[0, -1.5, 0]} center style={{ pointerEvents: 'none' }}>
        <div className="text-center">
          <p className="text-sm font-semibold text-white whitespace-nowrap">{phase.name}</p>
          <p className="text-xs text-slate-400 whitespace-nowrap">{phase.duration}</p>
        </div>
      </Html>

      {/* Selection glow */}
      {isSelected && (
        <mesh position={[0, 0, -0.2]}>
          <planeGeometry args={[2, 2.5]} />
          <meshBasicMaterial color={phase.color} transparent opacity={0.2} />
        </mesh>
      )}
    </group>
  );
}

function FlowArrows() {
  const arrowsRef = useRef<THREE.Group>(null);

  useFrame((state) => {
    if (arrowsRef.current) {
      arrowsRef.current.rotation.y = state.clock.elapsedTime * 0.1;
    }
  });

  return (
    <group ref={arrowsRef}>
      {PPBE_PHASES.map((_, index) => {
        const angle = (index / PPBE_PHASES.length) * Math.PI * 2 - Math.PI / 2;
        const nextAngle = ((index + 1) / PPBE_PHASES.length) * Math.PI * 2 - Math.PI / 2;
        const midAngle = (angle + nextAngle) / 2;
        const radius = 3;

        return (
          <mesh
            key={index}
            position={[
              Math.cos(midAngle) * radius,
              0,
              Math.sin(midAngle) * radius
            ]}
            rotation={[0, -midAngle + Math.PI / 2, 0]}
          >
            <coneGeometry args={[0.1, 0.3, 8]} />
            <meshBasicMaterial color="#64748b" transparent opacity={0.6} />
          </mesh>
        );
      })}
    </group>
  );
}

function CycleRing() {
  const ringRef = useRef<THREE.Mesh>(null);

  useFrame((state) => {
    if (ringRef.current) {
      ringRef.current.rotation.z = state.clock.elapsedTime * 0.2;
    }
  });

  return (
    <group position={[0, -0.5, 0]} rotation={[Math.PI / 2, 0, 0]}>
      {/* Main ring */}
      <mesh ref={ringRef}>
        <torusGeometry args={[3, 0.02, 16, 100]} />
        <meshBasicMaterial color="#3b82f6" transparent opacity={0.5} />
      </mesh>

      {/* Dashed outer ring */}
      <mesh>
        <torusGeometry args={[3.3, 0.01, 16, 100]} />
        <meshBasicMaterial color="#64748b" transparent opacity={0.3} />
      </mesh>

      {/* Center label */}
      <Html position={[0, 0, 0.5]} center style={{ pointerEvents: 'none' }}>
        <div className="bg-slate-900/90 backdrop-blur px-3 py-1.5 rounded-lg">
          <p className="text-xs font-semibold text-slate-300">Continuous Cycle</p>
        </div>
      </Html>
    </group>
  );
}
