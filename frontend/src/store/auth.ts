import { create } from 'zustand';
import Cookies from 'js-cookie';

interface User {
  id: string;
  email: string;
  username: string;
  full_name?: string;
  avatar_url?: string;
}

interface AuthStore {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  setUser: (user: User | null) => void;
  setToken: (token: string | null) => void;
  logout: () => void;
  login: (token: string, user: User) => void;
  checkAuth: () => void;
}

export const useAuthStore = create<AuthStore>((set) => ({
  user: null,
  token: Cookies.get('auth_token') || null,
  isLoading: false,
  isAuthenticated: !!Cookies.get('auth_token'),
  
  setUser: (user) => set({ user }),
  
  setToken: (token) => {
    if (token) {
      Cookies.set('auth_token', token, { expires: 7 });
      set({ token, isAuthenticated: true });
    } else {
      Cookies.remove('auth_token');
      set({ token: null, isAuthenticated: false, user: null });
    }
  },
  
  login: (token, user) => {
    Cookies.set('auth_token', token, { expires: 7 });
    set({ token, user, isAuthenticated: true });
  },
  
  logout: () => {
    Cookies.remove('auth_token');
    set({ token: null, user: null, isAuthenticated: false });
  },
  
  checkAuth: () => {
    const token = Cookies.get('auth_token');
    set({ isAuthenticated: !!token, token: token || null });
  },
}));
