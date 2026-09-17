import { createContext, useContext, useState, useEffect } from 'react';
import type { ReactNode } from 'react';

interface RouterContextType {
  pathname: string;
  currentPath: string;
  navigate: (to: string) => void;
}

const RouterContext = createContext<RouterContextType>({
  pathname: typeof window !== 'undefined' ? window.location.pathname : '/',
  currentPath: typeof window !== 'undefined' ? window.location.pathname : '/',
  navigate: () => {},
});

export const useRouter = () => useContext(RouterContext);

export interface RouterProps {
  children: ReactNode;
  initialPath?: string;
}

export function Router({ children, initialPath }: RouterProps) {
  const [pathname, setPathname] = useState<string>(
    initialPath || (typeof window !== 'undefined' ? window.location.pathname : '/')
  );

  useEffect(() => {
    const onPopState = () => {
      setPathname(window.location.pathname);
    };

    window.addEventListener('popstate', onPopState);
    return () => window.removeEventListener('popstate', onPopState);
  }, []);

  const navigate = (to: string) => {
    if (to === pathname) return;
    window.history.pushState({}, '', to);
    setPathname(to);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <RouterContext.Provider value={{ pathname, currentPath: pathname, navigate }}>
      {children}
    </RouterContext.Provider>
  );
}
