"use client";

import { useEffect } from "react";

// Popup landing page after step-up MFA; hands the verified marker back to the
// main window via the storage event, then closes itself.
// Next.js App Router requires a default export for page files.
export default function AuthCompletePage() {
  useEffect(() => {
    localStorage.setItem("innsight-mfa-verified", "1");
    window.close();
  }, []);
  return (
    <main className="grid h-screen place-items-center bg-ink text-white">
      <p className="text-[14px]">Identity verified. You can close this window.</p>
    </main>
  );
}
