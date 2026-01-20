'use client';

import { Canvas } from '@react-three/fiber';
import { Suspense, type ReactNode } from 'react';

interface CanvasWrapperProps {
  children: ReactNode;
  className?: string;
}

export function CanvasWrapper({ children, className }: CanvasWrapperProps) {
  return (
    <div className={className}>
      <Canvas
        camera={{ position: [0, 0, 5], fov: 50 }}
        dpr={[1, 2]}
        gl={{ antialias: true, alpha: true }}
      >
        <Suspense fallback={null}>
          <ambientLight intensity={0.5} />
          <pointLight position={[10, 10, 10]} intensity={1} />
          {children}
        </Suspense>
      </Canvas>
    </div>
  );
}
