import path from "path";
import { loadEnvConfig } from "@next/env";
import type { NextConfig } from "next";

// Single source of truth: repo-root `.env` (not web/.env.local).
loadEnvConfig(path.join(__dirname, ".."));

// Explicitly expose NEXT_PUBLIC_* so the client bundle always sees root flags
// (Auth0 Sign in / Log out depends on NEXT_PUBLIC_FLAG_AUTH0).
const publicEnv = Object.fromEntries(
  Object.entries(process.env).filter(([key]) => key.startsWith("NEXT_PUBLIC_")),
);

const nextConfig: NextConfig = {
  reactStrictMode: true,
  env: publicEnv,
};

export default nextConfig;
