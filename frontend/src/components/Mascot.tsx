import React from "react";

/** "Bit", the app's own character: a green bug with gold antennae. Decorative. */
export const Mascot: React.FC<{ size?: number; bob?: boolean }> = ({ size = 40, bob = false }) => (
  <svg className={`mascot ${bob ? "bob" : ""}`} width={size} height={size} viewBox="0 0 64 64" aria-hidden="true">
    <path d="M22 14 L16 4 M42 14 L48 4" stroke="#379e46" strokeWidth="4" strokeLinecap="round" />
    <circle cx="16" cy="4" r="4" fill="#ffc93c" />
    <circle cx="48" cy="4" r="4" fill="#ffc93c" />
    <rect x="6" y="16" width="52" height="46" rx="18" fill="#379e46" />
    <rect x="6" y="12" width="52" height="44" rx="18" fill="#55c764" />
    <circle cx="23" cy="32" r="9" fill="#fff" />
    <circle cx="41" cy="32" r="9" fill="#fff" />
    <circle cx="25" cy="33" r="4.5" fill="#17222c" />
    <circle cx="39" cy="33" r="4.5" fill="#17222c" />
    <path d="M26 46 Q32 51 38 46" stroke="#17222c" strokeWidth="3.5" strokeLinecap="round" fill="none" />
  </svg>
);
