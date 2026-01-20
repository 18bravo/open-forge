'use client';

import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import { Torus, Sphere } from '@react-three/drei';
import * as THREE from 'three';

function CodeParticle({ index, total }: { index: number; total: number }) {
  const ref = useRef<THREE.Mesh>(null);
  const initialAngle = (index / total) * Math.PI * 2;

  const isPass = index % 5 !== 0;
  const color = isPass ? '#22c55e' : '#f59e0b';

  useFrame((state) => {
    if (ref.current) {
      const time = state.clock.elapsedTime;
      const speed = 0.3;
      const angle = initialAngle + time * speed;

      const R = 1.2;
      const r = 0.4;
      const twist = angle * 0.5;

      const x = (R + r * Math.cos(twist)) * Math.cos(angle);
      const y = r * Math.sin(twist);
      const z = (R + r * Math.cos(twist)) * Math.sin(angle);

      ref.current.position.set(x, y, z);

      const atCheckpoint = Math.abs(Math.sin(angle * 2)) < 0.1;
      const scale = atCheckpoint ? 1.5 : 1;
      ref.current.scale.setScalar(scale);
    }
  });

  return (
    <Sphere ref={ref} args={[0.06, 16, 16]}>
      <meshStandardMaterial
        color={color}
        emissive={color}
        emissiveIntensity={0.7}
        roughness={0.3}
        metalness={0.7}
      />
    </Sphere>
  );
}

export function CodeLoopAnimation() {
  const groupRef = useRef<THREE.Group>(null);
  const particleCount = 15;

  const particles = useMemo(() =>
    Array.from({ length: particleCount }, (_, i) => i),
    []
  );

  useFrame((state) => {
    if (groupRef.current) {
      groupRef.current.rotation.x = Math.sin(state.clock.elapsedTime * 0.2) * 0.1;
      groupRef.current.rotation.z = Math.cos(state.clock.elapsedTime * 0.15) * 0.1;
    }
  });

  return (
    <group ref={groupRef}>
      <Torus args={[1.2, 0.02, 16, 100]} rotation={[Math.PI / 2, 0, 0]}>
        <meshStandardMaterial
          color="#8b5cf6"
          emissive="#8b5cf6"
          emissiveIntensity={0.3}
          transparent
          opacity={0.6}
        />
      </Torus>

      {particles.map((i) => (
        <CodeParticle key={i} index={i} total={particleCount} />
      ))}
    </group>
  );
}
