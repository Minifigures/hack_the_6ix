import path from "path";
import { loadEnvConfig } from "@next/env";
import type { NextConfig } from "next";

// Single source of truth: repo-root `.env`.
loadEnvConfig(path.join(__dirname, ".."));

const nextConfig: NextConfig = {
  reactStrictMode: true,
};

export default nextConfig;
