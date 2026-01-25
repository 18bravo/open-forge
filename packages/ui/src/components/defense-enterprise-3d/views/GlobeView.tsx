'use client';

/**
 * Globe View - 3D Earth with Combatant Command markers
 */

import { useRef, useMemo, useState } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { OrbitControls, Stars, Html, useTexture } from '@react-three/drei';
import * as THREE from 'three';
import { GEOGRAPHIC_COMMANDS, FUNCTIONAL_COMMANDS } from '../data';
import type { CombatantCommand } from '../types';

interface GlobeViewProps {
  selectedId: string | null;
  onSelect: (id: string) => void;
  showGeographic: boolean;
  showFunctional: boolean;
}

export function GlobeView({ selectedId, onSelect, showGeographic, showFunctional }: GlobeViewProps) {
  return (
    <div className="w-full h-full">
      <Canvas camera={{ position: [0, 0, 4], fov: 45 }}>
        <ambientLight intensity={0.3} />
        <pointLight position={[10, 10, 10]} intensity={1} />
        <pointLight position={[-10, -10, -10]} intensity={0.5} color="#4488ff" />

        <Globe />

        {showGeographic && GEOGRAPHIC_COMMANDS.map(cmd => (
          <CommandMarker
            key={cmd.id}
            command={cmd}
            isSelected={selectedId === cmd.id}
            onSelect={onSelect}
          />
        ))}

        {showFunctional && (
          <FunctionalCommandsPanel
            commands={FUNCTIONAL_COMMANDS}
            selectedId={selectedId}
            onSelect={onSelect}
          />
        )}

        <Stars radius={100} depth={50} count={3000} factor={4} fade speed={1} />
        <OrbitControls
          enablePan={false}
          minDistance={2.5}
          maxDistance={8}
          autoRotate
          autoRotateSpeed={0.3}
        />
      </Canvas>

      {/* Legend */}
      <div className="absolute bottom-6 left-6 bg-slate-900/90 backdrop-blur-xl rounded-lg border border-slate-700/50 p-4">
        <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Legend</h3>
        <div className="space-y-2">
          {showGeographic && (
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-blue-500" />
              <span className="text-sm text-slate-300">Geographic Commands (6)</span>
            </div>
          )}
          {showFunctional && (
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-purple-500" />
              <span className="text-sm text-slate-300">Functional Commands (5)</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function Globe() {
  const meshRef = useRef<THREE.Mesh>(null);

  useFrame((_, delta) => {
    if (meshRef.current) {
      meshRef.current.rotation.y += delta * 0.05;
    }
  });

  return (
    <group>
      {/* Earth sphere */}
      <mesh ref={meshRef}>
        <sphereGeometry args={[1, 64, 64]} />
        <meshStandardMaterial
          color="#1e3a5f"
          emissive="#0d1f35"
          emissiveIntensity={0.3}
          roughness={0.8}
          metalness={0.2}
        />
      </mesh>

      {/* Grid lines */}
      <mesh>
        <sphereGeometry args={[1.005, 32, 32]} />
        <meshBasicMaterial
          color="#3b82f6"
          wireframe
          transparent
          opacity={0.1}
        />
      </mesh>

      {/* Atmosphere glow */}
      <mesh scale={1.15}>
        <sphereGeometry args={[1, 32, 32]} />
        <meshBasicMaterial
          color="#3b82f6"
          transparent
          opacity={0.1}
          side={THREE.BackSide}
        />
      </mesh>
    </group>
  );
}

interface CommandMarkerProps {
  command: CombatantCommand;
  isSelected: boolean;
  onSelect: (id: string) => void;
}

function CommandMarker({ command, isSelected, onSelect }: CommandMarkerProps) {
  const [hovered, setHovered] = useState(false);
  const meshRef = useRef<THREE.Mesh>(null);

  // Convert lat/lon to 3D position
  const position = useMemo(() => {
    if (!command.lat || !command.lon) return new THREE.Vector3(0, 0, 0);
    const phi = (90 - command.lat) * (Math.PI / 180);
    const theta = (command.lon + 180) * (Math.PI / 180);
    const x = -Math.sin(phi) * Math.cos(theta) * 1.02;
    const y = Math.cos(phi) * 1.02;
    const z = Math.sin(phi) * Math.sin(theta) * 1.02;
    return new THREE.Vector3(x, y, z);
  }, [command.lat, command.lon]);

  useFrame((_, delta) => {
    if (meshRef.current) {
      const targetScale = hovered || isSelected ? 1.5 : 1;
      meshRef.current.scale.lerp(
        new THREE.Vector3(targetScale, targetScale, targetScale),
        delta * 5
      );
    }
  });

  return (
    <group position={position}>
      {/* Marker */}
      <mesh
        ref={meshRef}
        onClick={() => onSelect(command.id)}
        onPointerOver={() => setHovered(true)}
        onPointerOut={() => setHovered(false)}
      >
        <sphereGeometry args={[0.03, 16, 16]} />
        <meshStandardMaterial
          color={command.color}
          emissive={command.color}
          emissiveIntensity={isSelected ? 0.8 : hovered ? 0.5 : 0.3}
        />
      </mesh>

      {/* Pulse ring */}
      {(isSelected || hovered) && (
        <PulseRing color={command.color} />
      )}

      {/* Label */}
      {(hovered || isSelected) && (
        <Html
          position={[0, 0.08, 0]}
          center
          style={{ pointerEvents: 'none' }}
        >
          <div className="bg-slate-900/95 backdrop-blur px-3 py-1.5 rounded-lg border border-slate-700/50 whitespace-nowrap">
            <p className="text-sm font-semibold text-white">{command.abbrev}</p>
            <p className="text-xs text-slate-400">{command.hq}</p>
          </div>
        </Html>
      )}
    </group>
  );
}

function PulseRing({ color }: { color: string }) {
  const ringRef = useRef<THREE.Mesh>(null);

  useFrame((state) => {
    if (ringRef.current) {
      const scale = 1 + Math.sin(state.clock.elapsedTime * 3) * 0.3;
      ringRef.current.scale.set(scale, scale, scale);
      (ringRef.current.material as THREE.MeshBasicMaterial).opacity =
        0.5 - Math.sin(state.clock.elapsedTime * 3) * 0.3;
    }
  });

  return (
    <mesh ref={ringRef} rotation={[Math.PI / 2, 0, 0]}>
      <ringGeometry args={[0.04, 0.06, 32]} />
      <meshBasicMaterial color={color} transparent opacity={0.5} side={THREE.DoubleSide} />
    </mesh>
  );
}

interface FunctionalCommandsPanelProps {
  commands: CombatantCommand[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}

function FunctionalCommandsPanel({ commands, selectedId, onSelect }: FunctionalCommandsPanelProps) {
  const { viewport } = useThree();
  const startY = 0.8;
  const spacing = 0.35;

  return (
    <group position={[viewport.width / 2 - 0.8, startY, 0]}>
      <Html position={[0, 0.3, 0]} center style={{ pointerEvents: 'none' }}>
        <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider whitespace-nowrap">
          Functional Commands
        </p>
      </Html>

      {commands.map((cmd, index) => (
        <FunctionalMarker
          key={cmd.id}
          command={cmd}
          position={[0, -index * spacing, 0]}
          isSelected={selectedId === cmd.id}
          onSelect={onSelect}
        />
      ))}
    </group>
  );
}

interface FunctionalMarkerProps {
  command: CombatantCommand;
  position: [number, number, number];
  isSelected: boolean;
  onSelect: (id: string) => void;
}

function FunctionalMarker({ command, position, isSelected, onSelect }: FunctionalMarkerProps) {
  const [hovered, setHovered] = useState(false);

  return (
    <group position={position}>
      <Html center>
        <button
          onClick={() => onSelect(command.id)}
          onMouseEnter={() => setHovered(true)}
          onMouseLeave={() => setHovered(false)}
          className={`
            flex items-center gap-2 px-3 py-2 rounded-lg transition-all
            ${isSelected || hovered
              ? 'bg-slate-800 border-slate-600'
              : 'bg-slate-900/80 border-slate-700/50'
            }
            border backdrop-blur
          `}
        >
          <div
            className="w-2.5 h-2.5 rounded-full"
            style={{ backgroundColor: command.color }}
          />
          <span className="text-sm font-medium text-white whitespace-nowrap">
            {command.abbrev}
          </span>
        </button>
      </Html>
    </group>
  );
}
