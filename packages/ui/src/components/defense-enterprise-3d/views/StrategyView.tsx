'use client';

/**
 * Strategy View - Strategic guidance cascade visualization
 */

import { useRef, useState } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Html, RoundedBox } from '@react-three/drei';
import * as THREE from 'three';
import { STRATEGIC_DOCUMENTS, STRATEGY_FLOWS } from '../data';
import type { StrategicDocument } from '../types';

interface StrategyViewProps {
  selectedId: string | null;
  onSelect: (id: string) => void;
}

export function StrategyView({ selectedId, onSelect }: StrategyViewProps) {
  return (
    <div className="w-full h-full">
      <Canvas camera={{ position: [0, 0, 8], fov: 50 }}>
        <ambientLight intensity={0.4} />
        <pointLight position={[10, 10, 10]} intensity={1} />
        <pointLight position={[-5, -5, 5]} intensity={0.3} color="#f97316" />

        {/* Strategy cascade */}
        {STRATEGIC_DOCUMENTS.map((doc, index) => (
          <StrategyDocument
            key={doc.id}
            document={doc}
            index={index}
            isSelected={selectedId === doc.id}
            onSelect={onSelect}
          />
        ))}

        {/* Flow lines */}
        {STRATEGY_FLOWS.map((flow, index) => (
          <FlowLine key={index} flow={flow} />
        ))}

        {/* Background pyramid effect */}
        <PyramidBackground />

        <OrbitControls
          enablePan
          minDistance={4}
          maxDistance={15}
        />
      </Canvas>

      {/* Legend */}
      <div className="absolute bottom-6 left-6 bg-slate-900/90 backdrop-blur-xl rounded-lg border border-slate-700/50 p-4">
        <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
          Strategy Cascade
        </h3>
        <p className="text-xs text-slate-400 mb-3">
          Guidance flows from national to operational level
        </p>
        <div className="space-y-1">
          {STRATEGIC_DOCUMENTS.map(doc => (
            <div key={doc.id} className="flex items-center gap-2">
              <div
                className="w-2 h-2 rounded-full"
                style={{ backgroundColor: doc.color }}
              />
              <span className="text-xs text-slate-300">{doc.abbrev}</span>
              <span className="text-xs text-slate-500">- {doc.source}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

interface StrategyDocumentProps {
  document: StrategicDocument;
  index: number;
  isSelected: boolean;
  onSelect: (id: string) => void;
}

function StrategyDocument({ document, index, isSelected, onSelect }: StrategyDocumentProps) {
  const [hovered, setHovered] = useState(false);
  const groupRef = useRef<THREE.Group>(null);
  const meshRef = useRef<THREE.Mesh>(null);

  // Position in cascade (top to bottom)
  const yPos = 2.5 - index * 1.3;
  const xSpread = index * 0.2; // Slight spreading as we go down
  const width = 1.5 + index * 0.3; // Wider at bottom

  useFrame((state, delta) => {
    if (groupRef.current) {
      // Subtle float
      groupRef.current.position.x = Math.sin(state.clock.elapsedTime * 0.5 + index) * 0.05;
    }

    if (meshRef.current) {
      // Scale on interaction
      const targetScale = (hovered || isSelected) ? 1.15 : 1;
      meshRef.current.scale.lerp(
        new THREE.Vector3(targetScale, targetScale, targetScale),
        delta * 5
      );
    }
  });

  return (
    <group ref={groupRef} position={[0, yPos, 0]}>
      <RoundedBox
        ref={meshRef}
        args={[width, 0.8, 0.2]}
        radius={0.05}
        smoothness={4}
        onClick={() => onSelect(document.id)}
        onPointerOver={() => setHovered(true)}
        onPointerOut={() => setHovered(false)}
      >
        <meshStandardMaterial
          color={document.color}
          emissive={document.color}
          emissiveIntensity={isSelected ? 0.5 : hovered ? 0.3 : 0.15}
          metalness={0.3}
          roughness={0.7}
        />
      </RoundedBox>

      {/* Document icon/indicator */}
      <mesh position={[-width / 2 + 0.2, 0, 0.15]}>
        <boxGeometry args={[0.15, 0.4, 0.05]} />
        <meshBasicMaterial color="white" transparent opacity={0.3} />
      </mesh>

      {/* Label */}
      <Html position={[0, 0, 0.2]} center style={{ pointerEvents: 'none' }}>
        <div className="text-center">
          <p className="text-sm font-bold text-white">{document.abbrev}</p>
        </div>
      </Html>

      {/* Extended info on hover/select */}
      {(hovered || isSelected) && (
        <Html position={[width / 2 + 0.3, 0, 0]} style={{ pointerEvents: 'none' }}>
          <div className="bg-slate-900/95 backdrop-blur px-3 py-2 rounded-lg border border-slate-700/50 whitespace-nowrap">
            <p className="text-xs font-semibold text-white">{document.name}</p>
            <p className="text-xs text-slate-400 mt-1">{document.source}</p>
            {document.currentVersion && (
              <p className="text-xs text-slate-500 mt-1">Version: {document.currentVersion}</p>
            )}
          </div>
        </Html>
      )}

      {/* Selection indicator */}
      {isSelected && (
        <mesh position={[-width / 2 - 0.15, 0, 0]}>
          <boxGeometry args={[0.05, 0.6, 0.1]} />
          <meshBasicMaterial color={document.color} />
        </mesh>
      )}
    </group>
  );
}

interface FlowLineProps {
  flow: {
    fromId: string;
    toId: string;
    label: string;
  };
}

function FlowLine({ flow }: FlowLineProps) {
  const fromDoc = STRATEGIC_DOCUMENTS.find(d => d.id === flow.fromId);
  const toDoc = STRATEGIC_DOCUMENTS.find(d => d.id === flow.toId);

  if (!fromDoc || !toDoc) return null;

  const fromY = 2.5 - fromDoc.level * 1.3 - 0.4;
  const toY = 2.5 - toDoc.level * 1.3 + 0.4;

  const lineRef = useRef<THREE.Mesh>(null);

  useFrame((state) => {
    if (lineRef.current) {
      // Animate line opacity
      (lineRef.current.material as THREE.MeshBasicMaterial).opacity =
        0.3 + Math.sin(state.clock.elapsedTime * 2 + fromDoc.level) * 0.1;
    }
  });

  return (
    <group>
      {/* Arrow line */}
      <mesh ref={lineRef} position={[0, (fromY + toY) / 2, 0]}>
        <cylinderGeometry args={[0.01, 0.01, Math.abs(fromY - toY), 8]} />
        <meshBasicMaterial color="#64748b" transparent opacity={0.4} />
      </mesh>

      {/* Arrow head */}
      <mesh position={[0, toY + 0.1, 0]} rotation={[0, 0, Math.PI]}>
        <coneGeometry args={[0.05, 0.15, 8]} />
        <meshBasicMaterial color="#64748b" transparent opacity={0.6} />
      </mesh>

      {/* Flow label */}
      <Html position={[0.15, (fromY + toY) / 2, 0]} style={{ pointerEvents: 'none' }}>
        <span className="text-xs text-slate-500 italic">{flow.label}</span>
      </Html>
    </group>
  );
}

function PyramidBackground() {
  const pyramidRef = useRef<THREE.Mesh>(null);

  useFrame((state) => {
    if (pyramidRef.current) {
      pyramidRef.current.rotation.y = state.clock.elapsedTime * 0.05;
    }
  });

  return (
    <mesh ref={pyramidRef} position={[0, 0, -3]} rotation={[0, 0, Math.PI]}>
      <coneGeometry args={[4, 7, 4]} />
      <meshBasicMaterial
        color="#1e293b"
        transparent
        opacity={0.3}
        wireframe
      />
    </mesh>
  );
}
