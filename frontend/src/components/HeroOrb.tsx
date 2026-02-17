'use client';
import { useRef, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Sphere, MeshDistortMaterial, Float, OrbitControls } from '@react-three/drei';
import * as THREE from 'three';

function AnimatedSphere() {
  const meshRef = useRef<THREE.Mesh>(null);
  const materialRef = useRef<any>(null);

  useFrame(({ clock }) => {
    if (meshRef.current) {
      meshRef.current.rotation.x = clock.getElapsedTime() * 0.15;
      meshRef.current.rotation.y = clock.getElapsedTime() * 0.2;
    }
  });

  return (
    <Float speed={2} rotationIntensity={0.5} floatIntensity={1.5}>
      <Sphere ref={meshRef} args={[1.8, 128, 128]} scale={1}>
        <MeshDistortMaterial
          ref={materialRef}
          color="#7c3aed"
          emissive="#4c1d95"
          emissiveIntensity={0.4}
          roughness={0.2}
          metalness={0.8}
          distort={0.4}
          speed={2}
          transparent
          opacity={0.85}
        />
      </Sphere>
    </Float>
  );
}

function InnerGlow() {
  const ref = useRef<THREE.Mesh>(null);
  useFrame(({ clock }) => {
    if (ref.current) {
      ref.current.scale.setScalar(1 + Math.sin(clock.getElapsedTime() * 1.5) * 0.08);
    }
  });

  return (
    <Float speed={3} rotationIntensity={0.3} floatIntensity={0.8}>
      <Sphere ref={ref} args={[1.2, 64, 64]}>
        <meshStandardMaterial
          color="#06b6d4"
          emissive="#0891b2"
          emissiveIntensity={0.6}
          transparent
          opacity={0.3}
          wireframe
        />
      </Sphere>
    </Float>
  );
}

function Particles() {
  const count = 300;
  const ref = useRef<THREE.Points>(null);

  const positions = useMemo(() => {
    const pos = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      pos[i * 3] = (Math.random() - 0.5) * 12;
      pos[i * 3 + 1] = (Math.random() - 0.5) * 12;
      pos[i * 3 + 2] = (Math.random() - 0.5) * 12;
    }
    return pos;
  }, []);

  const sizes = useMemo(() => {
    const s = new Float32Array(count);
    for (let i = 0; i < count; i++) {
      s[i] = Math.random() * 0.03 + 0.01;
    }
    return s;
  }, []);

  useFrame(({ clock }) => {
    if (ref.current) {
      ref.current.rotation.y = clock.getElapsedTime() * 0.03;
      ref.current.rotation.x = clock.getElapsedTime() * 0.02;
    }
  });

  return (
    <points ref={ref}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[positions, 3]} />
      </bufferGeometry>
      <pointsMaterial
        size={0.03}
        color="#7c3aed"
        transparent
        opacity={0.6}
        sizeAttenuation
      />
    </points>
  );
}

function Rings() {
  const ref1 = useRef<THREE.Mesh>(null);
  const ref2 = useRef<THREE.Mesh>(null);
  const ref3 = useRef<THREE.Mesh>(null);

  useFrame(({ clock }) => {
    const t = clock.getElapsedTime();
    if (ref1.current) { ref1.current.rotation.x = t * 0.3; ref1.current.rotation.z = t * 0.1; }
    if (ref2.current) { ref2.current.rotation.y = t * 0.2; ref2.current.rotation.x = t * 0.15; }
    if (ref3.current) { ref3.current.rotation.z = t * 0.25; ref3.current.rotation.y = t * 0.1; }
  });

  return (
    <>
      <mesh ref={ref1}>
        <torusGeometry args={[2.8, 0.008, 16, 100]} />
        <meshStandardMaterial color="#7c3aed" emissive="#7c3aed" emissiveIntensity={0.8} transparent opacity={0.4} />
      </mesh>
      <mesh ref={ref2}>
        <torusGeometry args={[3.2, 0.006, 16, 100]} />
        <meshStandardMaterial color="#06b6d4" emissive="#06b6d4" emissiveIntensity={0.6} transparent opacity={0.3} />
      </mesh>
      <mesh ref={ref3}>
        <torusGeometry args={[3.6, 0.004, 16, 100]} />
        <meshStandardMaterial color="#ec4899" emissive="#ec4899" emissiveIntensity={0.5} transparent opacity={0.2} />
      </mesh>
    </>
  );
}

export default function HeroOrb() {
  return (
    <div className="w-full h-full" style={{ minHeight: '500px' }}>
      <Canvas
        camera={{ position: [0, 0, 6], fov: 50 }}
        dpr={[1, 2]}
        gl={{ antialias: true, alpha: true }}
        style={{ background: 'transparent' }}
      >
        <ambientLight intensity={0.3} />
        <pointLight position={[5, 5, 5]} intensity={0.8} color="#7c3aed" />
        <pointLight position={[-5, -3, 3]} intensity={0.5} color="#06b6d4" />
        <pointLight position={[0, 5, -5]} intensity={0.3} color="#ec4899" />
        <AnimatedSphere />
        <InnerGlow />
        <Particles />
        <Rings />
        <OrbitControls enableZoom={false} enablePan={false} autoRotate autoRotateSpeed={0.5} />
      </Canvas>
    </div>
  );
}
