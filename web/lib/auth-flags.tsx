"use client";

import { createContext, useContext } from "react";

/** Server-injected Auth0 flag — avoids fragile NEXT_PUBLIC inlining from a parent `.env`. */
const AuthFlagsContext = createContext({ auth0: false });

export function AuthFlagsProvider({
  auth0,
  children,
}: {
  auth0: boolean;
  children: React.ReactNode;
}) {
  return (
    <AuthFlagsContext.Provider value={{ auth0 }}>
      {children}
    </AuthFlagsContext.Provider>
  );
}

export function useAuth0Flag(): boolean {
  return useContext(AuthFlagsContext).auth0;
}
