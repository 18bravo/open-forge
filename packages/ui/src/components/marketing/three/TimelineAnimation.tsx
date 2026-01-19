'use client';

import { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { Box, Text } from '@react-three/drei';
import * as THREE from 'three';

function TimelineBlock({
  label,
  index,
  total
}: {
  label: string;
  index: number;
  total: number;
}) {
  const ref = useRef<THREE.Mesh>(null);
  const textRef = useRef<THREE.Mesh>(null);
  const initialX = (index - total / 2) * 0.8;

  useFrame((state) => {
    if (ref.current && textRef.current) {
      const time = state.clock.elapsedTime;
      const cycleTime = 4;
      const t = (time % cycleTime) / cycleTime;

      let compressionFactor: number;
      if (t < 0.4) {
        compressionFactor = 1 - (t / 0.4) * 0.9;
      } else if (t < 0.6) {
        compressionFactor = 0.1;
      } else {
        compressionFactor = 0.1 + ((t - 0.6) / 0.4) * 0.9;
      }

      const x = initialX * compressionFactor;
      ref.current.position.x = x;
      textRef.current.position.x = x;

      const isDay1 = index === total - 1;
      if (isDay1 && t > 0.35 && t < 0.65) {
        ref.current.scale.setScalar(1.5);
        // @ts-ignore
        ref.current.material.emissiveIntensity = 1;
      } else {
        ref.current.scale.setScalar(1);
        // @ts-ignore
        ref.current.material.emissiveIntensity = 0.3;
      }
    }
  });

  const color = index === 3 ? '#22c55e' : '#8b5cf6';

  return (
    <group>
      <Box ref={ref} args={[0.5, 0.3, 0.1]} position={[initialX, 0, 0]}>
        <meshStandardMaterial
          color={color}
          emissive={color}
          emissiveIntensity={0.3}
          roughness={0.4}
          metalness={0.6}
        />
      </Box>
      <Text
        ref={textRef}
        position={[initialX, 0, 0.1]}
        fontSize={0.1}
        color="white"
        anchorX="center"
        anchorY="middle"
      >
        {label}
      </Text>
    </group>
  );
}

export function TimelineAnimation() {
  const groupRef = useRef<THREE.Group>(null);
  const labels = ['Year 1', 'Year 2', 'Year 3', 'Day 1'];

  return (
    <group ref={groupRef}>
      {labels.map((label, i) => (
        <TimelineBlock
          key={i}
          label={label}
          index={i}
          total={labels.length}
        />
      ))}
    </group>
  );
}
