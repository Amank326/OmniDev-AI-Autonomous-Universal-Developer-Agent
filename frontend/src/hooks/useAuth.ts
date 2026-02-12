import { useAuthStore } from '@/store/auth';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

export function useAuth() {
  const router = useRouter();
  const { user, token, isAuthenticated } = useAuthStore();

  useEffect(() => {
    if (!isAuthenticated && typeof window !== 'undefined') {
      router.push('/auth/login');
    }
  }, [isAuthenticated, router]);

  return { user, token, isAuthenticated };
}

export function useUser() {
  const { user } = useAuthStore();
  return user;
}

export function useLogout() {
  const { logout } = useAuthStore();
  const router = useRouter();

  return () => {
    logout();
    router.push('/auth/login');
  };
}
