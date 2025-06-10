import { createContext, useContext, useEffect, useState } from 'react';
import axios from 'axios';

interface User {
  id: number;
  username: string;
  email?: string;
  roles: string;
}

interface AuthContextValue {
  user: User | null;
  token: string | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('AuthContext not provided');
  return ctx;
};

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);

  const logout = async () => {
    if (token) {
      try {
        await axios.post(
          'http://localhost:8001/logout',
          {},
          { headers: { Authorization: `Bearer ${token}` } },
        );
      } catch {
        /* ignore */
      }
    }
    setUser(null);
    setToken(null);
    localStorage.removeItem('auth_token');
    localStorage.removeItem('auth_expires');
  };

  const login = async (username: string, password: string) => {
    const res = await axios.post('http://localhost:8001/login', {
      username,
      password,
    });
    const newToken = res.data.token as string;
    setToken(newToken);
    localStorage.setItem('auth_token', newToken);
    localStorage.setItem('auth_expires', String(Date.now() + 30 * 60 * 1000));
    const me = await axios.get<User>('http://localhost:8001/me', {
      headers: { Authorization: `Bearer ${newToken}` },
    });
    setUser(me.data);
  };

  useEffect(() => {
    const stored = localStorage.getItem('auth_token');
    const exp = localStorage.getItem('auth_expires');
    if (stored && exp && Date.now() < Number(exp)) {
      setToken(stored);
      axios
        .get<User>('http://localhost:8001/me', {
          headers: { Authorization: `Bearer ${stored}` },
        })
        .then((res) => setUser(res.data))
        .catch(() => logout());
    }
  }, []);

  useEffect(() => {
    const updateExpiry = () => {
      if (token) {
        localStorage.setItem('auth_expires', String(Date.now() + 30 * 60 * 1000));
      }
    };
    document.addEventListener('click', updateExpiry);
    document.addEventListener('keydown', updateExpiry);
    const interval = setInterval(() => {
      const exp = Number(localStorage.getItem('auth_expires') || 0);
      if (token && Date.now() > exp) {
        logout();
      }
    }, 60000);
    return () => {
      document.removeEventListener('click', updateExpiry);
      document.removeEventListener('keydown', updateExpiry);
      clearInterval(interval);
    };
  }, [token]);

  return (
    <AuthContext.Provider value={{ user, token, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};
