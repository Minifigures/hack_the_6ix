import path from "path";
import fs from "fs";
import { loadEnvConfig } from "@next/env";
import type { NextConfig } from "next";

// Local: load repo-root `.env` when present. On Vercel the file is absent —
// platform env vars are already in process.env.
const rootDir = path.join(__dirname, "..");
if (fs.existsSync(path.join(rootDir, ".env")) || fs.existsSync(rootDir)) {
  loadEnvConfig(rootDir);
}

// Expose NEXT_PUBLIC_* into the client bundle (flags, API base, etc.).
const publicEnv = Object.fromEntries(
  Object.entries(process.env).filter(([key]) => key.startsWith("NEXT_PUBLIC_")),
);

const nextConfig: NextConfig = {
  reactStrictMode: true,
  env: publicEnv,
};

export default nextConfig;
