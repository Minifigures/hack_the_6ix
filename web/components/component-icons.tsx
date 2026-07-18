import type { JSX } from "react";

// Soft flat-illustration icon set for the Design Options panel, left icon
// rail, and Physics & Structure log. Pure SVG, safe in server or client
// components.

const WINDOW_ROWS = [9.5, 14, 18.5] as const;
const WINDOW_COLS = [11.5, 16.5, 21.5] as const;
const TOWER_ROWS = [7, 11, 15, 19, 23, 27] as const;

export function TypeIcon({
  type,
}: {
  type: "hotel" | "homestay" | "bnb" | "tower";
}): JSX.Element {
  switch (type) {
    case "hotel":
      return (
        <svg width={40} height={40} viewBox="0 0 40 40" aria-hidden="true">
          <rect x={5} y={33.5} width={30} height={3.5} rx={1} fill="#ccd4dc" stroke="#9aa6b2" strokeWidth={1} />
          <rect x={9.5} y={7.5} width={17} height={26} fill="#dde6ee" stroke="#7c8ea2" strokeWidth={1} />
          <rect x={26.5} y={7.5} width={4.5} height={26} fill="#b7c6d4" stroke="#7c8ea2" strokeWidth={1} />
          <rect x={8.5} y={5} width={23.5} height={2.5} fill="#a9b8c7" stroke="#7c8ea2" strokeWidth={1} />
          {WINDOW_ROWS.map((y) =>
            WINDOW_COLS.map((x) => (
              <rect key={`${x}-${y}`} x={x} y={y} width={3} height={3} rx={0.5} fill="#6f95bb" />
            )),
          )}
          <rect x={16.5} y={27} width={5} height={6.5} fill="#55708c" />
          <path d="M14.5 27 L23.5 27 L22 23.8 L16 23.8 Z" fill="#d1685a" stroke="#a24b40" strokeWidth={1} strokeLinejoin="round" />
        </svg>
      );
    case "homestay":
      return (
        <svg width={40} height={40} viewBox="0 0 40 40" aria-hidden="true">
          <ellipse cx={20} cy={33.5} rx={14.5} ry={3.2} fill="#a9c98b" stroke="#7ba05e" strokeWidth={1} />
          <rect x={10} y={19} width={20} height={14} fill="#f4e8d3" stroke="#8a6a4f" strokeWidth={1} />
          <path d="M6 20.5 L20 7 L34 20.5 Z" fill="#b05f45" stroke="#7e4230" strokeWidth={1} strokeLinejoin="round" />
          <rect x={17.5} y={25.5} width={5} height={7.5} rx={1} fill="#7c4b33" />
          <rect x={12} y={22} width={4} height={4} rx={0.5} fill="#9dbfd3" stroke="#8a6a4f" strokeWidth={0.8} />
          <rect x={24} y={22} width={4} height={4} rx={0.5} fill="#9dbfd3" stroke="#8a6a4f" strokeWidth={0.8} />
        </svg>
      );
    case "bnb":
      return (
        <svg width={40} height={40} viewBox="0 0 40 40" aria-hidden="true">
          <ellipse cx={19} cy={33.5} rx={15} ry={3.2} fill="#a9c98b" stroke="#7ba05e" strokeWidth={1} />
          <rect x={22.5} y={9} width={3.5} height={9} fill="#9c6b52" stroke="#6f4a37" strokeWidth={1} />
          <path d="M5 21 L17 8 L29 21 Z" fill="#c25549" stroke="#8c3b32" strokeWidth={1} strokeLinejoin="round" />
          <rect x={8} y={21} width={18} height={12} fill="#f0e3cf" stroke="#8a6a4f" strokeWidth={1} />
          <rect x={11} y={26} width={4.5} height={7} rx={1} fill="#7c4b33" />
          <rect x={19} y={24} width={4.5} height={4.5} rx={0.5} fill="#9dbfd3" stroke="#8a6a4f" strokeWidth={0.8} />
          <line x1={32} y1={25} x2={32} y2={33} stroke="#8a6a4f" strokeWidth={1.5} />
          <rect x={28.5} y={21.5} width={7} height={4.5} rx={1} fill="#ecdcb4" stroke="#8a6a4f" strokeWidth={1} />
          <line x1={30} y1={23.7} x2={34} y2={23.7} stroke="#8a6a4f" strokeWidth={0.9} />
        </svg>
      );
    case "tower":
      return (
        <svg width={40} height={40} viewBox="0 0 40 40" aria-hidden="true">
          <ellipse cx={20} cy={34.5} rx={11} ry={2.8} fill="#a9c98b" stroke="#7ba05e" strokeWidth={1} />
          <rect x={14.5} y={4.5} width={8.5} height={30} fill="#c4d7e8" stroke="#6d89a6" strokeWidth={1} />
          <rect x={23} y={4.5} width={3} height={30} fill="#9db8cf" stroke="#6d89a6" strokeWidth={1} />
          <rect x={13.5} y={2.8} width={13.5} height={2} fill="#8ea9c0" stroke="#6d89a6" strokeWidth={0.8} />
          {TOWER_ROWS.map((y) => (
            <g key={y}>
              <rect x={16} y={y} width={2.4} height={2.4} rx={0.4} fill="#5f88ad" />
              <rect x={19.6} y={y} width={2.4} height={2.4} rx={0.4} fill="#5f88ad" />
            </g>
          ))}
        </svg>
      );
  }
}

export function ComponentIcon({
  kind,
}: {
  kind:
    | "reinforced_concrete"
    | "precast_piles"
    | "timber"
    | "steel_brace"
    | "mass_timber"
    | "hollow_core"
    | "curtain_wall"
    | "rainscreen"
    | "heat_pump"
    | "central_plant";
}): JSX.Element {
  switch (kind) {
    case "reinforced_concrete":
      return (
        <svg width={32} height={32} viewBox="0 0 32 32" aria-hidden="true">
          <polygon points="3,13 16,7 29,13 16,19" fill="#ced3d8" stroke="#878f98" strokeWidth={1} strokeLinejoin="round" />
          <polygon points="3,13 16,19 16,25 3,19" fill="#aab1b8" stroke="#878f98" strokeWidth={1} strokeLinejoin="round" />
          <polygon points="29,13 16,19 16,25 29,19" fill="#99a1a9" stroke="#878f98" strokeWidth={1} strokeLinejoin="round" />
          <circle cx={7} cy={17.4} r={1} fill="#676f78" />
          <circle cx={11.5} cy={19.6} r={1} fill="#676f78" />
          <circle cx={20.5} cy={19.6} r={1} fill="#676f78" />
          <circle cx={25} cy={17.4} r={1} fill="#676f78" />
        </svg>
      );
    case "precast_piles":
      return (
        <svg width={32} height={32} viewBox="0 0 32 32" aria-hidden="true">
          <rect x={6} y={10} width={5} height={16} rx={2.5} fill="#b8bec6" stroke="#80868f" strokeWidth={1} />
          <rect x={13.5} y={5} width={5} height={21} rx={2.5} fill="#c4cad1" stroke="#80868f" strokeWidth={1} />
          <rect x={21} y={12} width={5} height={14} rx={2.5} fill="#b8bec6" stroke="#80868f" strokeWidth={1} />
          <line x1={15} y1={8} x2={15} y2={23} stroke="#dee2e7" strokeWidth={1} />
        </svg>
      );
    case "timber":
      return (
        <svg width={32} height={32} viewBox="0 0 32 32" aria-hidden="true">
          <circle cx={10} cy={21} r={6} fill="#cf9250" stroke="#97622f" strokeWidth={1} />
          <circle cx={22} cy={21} r={6} fill="#cf9250" stroke="#97622f" strokeWidth={1} />
          <circle cx={16} cy={11.5} r={6} fill="#d99a55" stroke="#97622f" strokeWidth={1} />
          <circle cx={10} cy={21} r={2.8} fill="#e8c493" stroke="#a56a33" strokeWidth={0.8} />
          <circle cx={22} cy={21} r={2.8} fill="#e8c493" stroke="#a56a33" strokeWidth={0.8} />
          <circle cx={16} cy={11.5} r={2.8} fill="#e8c493" stroke="#a56a33" strokeWidth={0.8} />
          <circle cx={16} cy={11.5} r={0.9} fill="#97622f" />
          <circle cx={10} cy={21} r={0.9} fill="#97622f" />
          <circle cx={22} cy={21} r={0.9} fill="#97622f" />
        </svg>
      );
    case "steel_brace":
      return (
        <svg width={32} height={32} viewBox="0 0 32 32" aria-hidden="true">
          <line x1={5.5} y1={5.5} x2={26.5} y2={26.5} stroke="#8296aa" strokeWidth={2} strokeLinecap="round" />
          <line x1={26.5} y1={5.5} x2={5.5} y2={26.5} stroke="#8296aa" strokeWidth={2} strokeLinecap="round" />
          <rect x={5} y={5} width={22} height={22} rx={1} fill="none" stroke="#64788c" strokeWidth={2.5} />
          <rect x={3.4} y={3.4} width={4} height={4} rx={0.8} fill="#56697c" />
          <rect x={24.6} y={3.4} width={4} height={4} rx={0.8} fill="#56697c" />
          <rect x={3.4} y={24.6} width={4} height={4} rx={0.8} fill="#56697c" />
          <rect x={24.6} y={24.6} width={4} height={4} rx={0.8} fill="#56697c" />
          <circle cx={16} cy={16} r={2} fill="#56697c" />
        </svg>
      );
    case "mass_timber":
      return (
        <svg width={32} height={32} viewBox="0 0 32 32" aria-hidden="true">
          <polygon points="3,12 16,6 29,12 16,18" fill="#e5a75e" stroke="#a8702f" strokeWidth={1} strokeLinejoin="round" />
          <polygon points="3,12 16,18 16,25 3,19" fill="#cd8a41" stroke="#a8702f" strokeWidth={1} strokeLinejoin="round" />
          <polygon points="29,12 16,18 16,25 29,19" fill="#c07c35" stroke="#a8702f" strokeWidth={1} strokeLinejoin="round" />
          <line x1={7.3} y1={14} x2={20.3} y2={8} stroke="#a8702f" strokeWidth={0.9} />
          <line x1={11.7} y1={16} x2={24.7} y2={10} stroke="#a8702f" strokeWidth={0.9} />
          <path d="M3 15.5 L16 21.5 L29 15.5" fill="none" stroke="#a8702f" strokeWidth={0.9} />
        </svg>
      );
    case "hollow_core":
      return (
        <svg width={32} height={32} viewBox="0 0 32 32" aria-hidden="true">
          <rect x={3} y={10.5} width={26} height={11} rx={1.5} fill="#c6cbd1" stroke="#868e97" strokeWidth={1} />
          <line x1={4.5} y1={12.5} x2={27.5} y2={12.5} stroke="#dde1e5" strokeWidth={1} />
          <circle cx={8} cy={16.5} r={2.6} fill="#838b94" stroke="#6b737c" strokeWidth={0.8} />
          <circle cx={14} cy={16.5} r={2.6} fill="#838b94" stroke="#6b737c" strokeWidth={0.8} />
          <circle cx={20} cy={16.5} r={2.6} fill="#838b94" stroke="#6b737c" strokeWidth={0.8} />
          <circle cx={26} cy={16.5} r={2.6} fill="#838b94" stroke="#6b737c" strokeWidth={0.8} />
        </svg>
      );
    case "curtain_wall":
      return (
        <svg width={32} height={32} viewBox="0 0 32 32" aria-hidden="true">
          <rect x={5} y={4} width={22} height={24} rx={1} fill="#bfdeeb" stroke="#64889b" strokeWidth={1.2} />
          <line x1={12.3} y1={4} x2={12.3} y2={28} stroke="#7fa9ba" strokeWidth={1} />
          <line x1={19.7} y1={4} x2={19.7} y2={28} stroke="#7fa9ba" strokeWidth={1} />
          <line x1={5} y1={12} x2={27} y2={12} stroke="#7fa9ba" strokeWidth={1} />
          <line x1={5} y1={20} x2={27} y2={20} stroke="#7fa9ba" strokeWidth={1} />
          <line x1={7.5} y1={10} x2={11} y2={6} stroke="#e9f5fa" strokeWidth={1.4} strokeLinecap="round" />
        </svg>
      );
    case "rainscreen":
      return (
        <svg width={32} height={32} viewBox="0 0 32 32" aria-hidden="true">
          <rect x={5} y={5} width={7} height={22} fill="#93a5b4" stroke="#66788a" strokeWidth={1} />
          <line x1={6} y1={11} x2={11} y2={6} stroke="#7c8fa0" strokeWidth={0.9} />
          <line x1={6} y1={19} x2={11} y2={14} stroke="#7c8fa0" strokeWidth={0.9} />
          <line x1={6} y1={26} x2={11} y2={21} stroke="#7c8fa0" strokeWidth={0.9} />
          <line x1={12} y1={10} x2={16} y2={10} stroke="#66788a" strokeWidth={1} />
          <line x1={12} y1={22} x2={16} y2={22} stroke="#66788a" strokeWidth={1} />
          <rect x={16} y={5} width={3} height={22} fill="#c2d1de" stroke="#66788a" strokeWidth={1} />
          <rect x={20.5} y={5} width={3} height={22} fill="#c2d1de" stroke="#66788a" strokeWidth={1} />
          <rect x={25} y={5} width={3} height={22} fill="#c2d1de" stroke="#66788a" strokeWidth={1} />
        </svg>
      );
    case "heat_pump":
      return (
        <svg width={32} height={32} viewBox="0 0 32 32" aria-hidden="true">
          <rect x={7} y={24.5} width={4} height={2.8} rx={0.8} fill="#a96f66" />
          <rect x={21} y={24.5} width={4} height={2.8} rx={0.8} fill="#a96f66" />
          <rect x={4} y={6} width={24} height={19} rx={2} fill="#f0d3cd" stroke="#a96f66" strokeWidth={1.2} />
          <circle cx={13} cy={15.5} r={6} fill="#f8e6e2" stroke="#a96f66" strokeWidth={1.2} />
          <line x1={9.8} y1={12.3} x2={16.2} y2={18.7} stroke="#c08e85" strokeWidth={1.2} strokeLinecap="round" />
          <line x1={16.2} y1={12.3} x2={9.8} y2={18.7} stroke="#c08e85" strokeWidth={1.2} strokeLinecap="round" />
          <circle cx={13} cy={15.5} r={1.8} fill="#a96f66" />
          <line x1={21.5} y1={10} x2={25.5} y2={10} stroke="#c9a099" strokeWidth={1.2} strokeLinecap="round" />
          <line x1={21.5} y1={13.5} x2={25.5} y2={13.5} stroke="#c9a099" strokeWidth={1.2} strokeLinecap="round" />
          <line x1={21.5} y1={17} x2={25.5} y2={17} stroke="#c9a099" strokeWidth={1.2} strokeLinecap="round" />
          <line x1={21.5} y1={20.5} x2={25.5} y2={20.5} stroke="#c9a099" strokeWidth={1.2} strokeLinecap="round" />
        </svg>
      );
    case "central_plant":
      return (
        <svg width={32} height={32} viewBox="0 0 32 32" aria-hidden="true">
          <rect x={3} y={26.5} width={26} height={3} rx={1} fill="#a9c491" stroke="#7ba05e" strokeWidth={0.9} />
          <rect x={9} y={4.5} width={3} height={9} fill="#a3ada0" stroke="#79856f" strokeWidth={1} />
          <rect x={8.4} y={3.2} width={4.2} height={1.8} fill="#79856f" />
          <rect x={14.5} y={6.5} width={3} height={7} fill="#a3ada0" stroke="#79856f" strokeWidth={1} />
          <rect x={13.9} y={5.2} width={4.2} height={1.8} fill="#79856f" />
          <rect x={6} y={14} width={14} height={13} fill="#b9c2b4" stroke="#79856f" strokeWidth={1} />
          <rect x={5.3} y={12.5} width={15.4} height={2} fill="#97a291" stroke="#79856f" strokeWidth={0.8} />
          <rect x={20} y={19} width={7.5} height={8} fill="#cad2c4" stroke="#79856f" strokeWidth={1} />
          <rect x={8.5} y={17} width={3} height={3} rx={0.4} fill="#6f7d68" />
          <rect x={14} y={17} width={3} height={3} rx={0.4} fill="#6f7d68" />
          <rect x={11} y={22} width={4} height={5} fill="#6f7d68" />
          <rect x={22.5} y={21.5} width={2.5} height={2.5} rx={0.4} fill="#6f7d68" />
        </svg>
      );
  }
}

export function RailThumb({ index }: { index: number }): JSX.Element {
  const variant = ((index % 5) + 5) % 5;
  switch (variant) {
    case 0:
      return (
        <svg width={30} height={30} viewBox="0 0 30 30" aria-hidden="true">
          <rect x={4} y={25} width={22} height={2.5} rx={0.8} fill="#ccd4dc" />
          <rect x={6} y={7} width={15} height={18} fill="#b9cbdc" stroke="#7c8ea2" strokeWidth={1} />
          <rect x={21} y={7} width={3.5} height={18} fill="#97acc0" stroke="#7c8ea2" strokeWidth={1} />
          <rect x={5} y={5} width={20.5} height={2} fill="#8ba0b4" />
          <rect x={8.5} y={10} width={2.6} height={2.6} fill="#5f88ad" />
          <rect x={13} y={10} width={2.6} height={2.6} fill="#5f88ad" />
          <rect x={8.5} y={15} width={2.6} height={2.6} fill="#5f88ad" />
          <rect x={13} y={15} width={2.6} height={2.6} fill="#5f88ad" />
          <rect x={11.5} y={20} width={4} height={5} fill="#55708c" />
        </svg>
      );
    case 1:
      return (
        <svg width={30} height={30} viewBox="0 0 30 30" aria-hidden="true">
          <rect x={4.5} y={7} width={21} height={2} fill="#c98f4c" />
          <rect x={5} y={9} width={20} height={16} fill="#dfa763" stroke="#a8702f" strokeWidth={1} />
          <line x1={5} y1={14.3} x2={25} y2={14.3} stroke="#b57f3a" strokeWidth={1} />
          <line x1={5} y1={19.6} x2={25} y2={19.6} stroke="#b57f3a" strokeWidth={1} />
          <rect x={18} y={19.6} width={7} height={5.4} fill="#c98f4c" stroke="#a8702f" strokeWidth={0.9} />
        </svg>
      );
    case 2:
      return (
        <svg width={30} height={30} viewBox="0 0 30 30" aria-hidden="true">
          <ellipse cx={15} cy={25.5} rx={9.5} ry={2.5} fill="#a9c98b" stroke="#7ba05e" strokeWidth={0.9} />
          <rect x={10.5} y={4} width={7} height={21} fill="#c4d7e8" stroke="#6d89a6" strokeWidth={1} />
          <rect x={17.5} y={4} width={2.5} height={21} fill="#9db8cf" stroke="#6d89a6" strokeWidth={1} />
          <rect x={12} y={7} width={2} height={2} fill="#5f88ad" />
          <rect x={15} y={7} width={2} height={2} fill="#5f88ad" />
          <rect x={12} y={11} width={2} height={2} fill="#5f88ad" />
          <rect x={15} y={11} width={2} height={2} fill="#5f88ad" />
          <rect x={12} y={15} width={2} height={2} fill="#5f88ad" />
          <rect x={15} y={15} width={2} height={2} fill="#5f88ad" />
          <rect x={12} y={19} width={2} height={2} fill="#5f88ad" />
          <rect x={15} y={19} width={2} height={2} fill="#5f88ad" />
        </svg>
      );
    case 3:
      return (
        <svg width={30} height={30} viewBox="0 0 30 30" aria-hidden="true">
          <rect x={4} y={25} width={22} height={2.5} rx={0.8} fill="#ccd4dc" />
          <rect x={5} y={6.5} width={20} height={2} fill="#8c4a3d" />
          <rect x={6} y={8.5} width={18} height={16.5} fill="#b06553" stroke="#7c4136" strokeWidth={1} />
          <rect x={8.5} y={11.5} width={3} height={3.5} fill="#e3cfc0" />
          <rect x={13.5} y={11.5} width={3} height={3.5} fill="#e3cfc0" />
          <rect x={18.5} y={11.5} width={3} height={3.5} fill="#e3cfc0" />
          <rect x={8.5} y={17.5} width={3} height={3.5} fill="#e3cfc0" />
          <rect x={18.5} y={17.5} width={3} height={3.5} fill="#e3cfc0" />
          <rect x={13.5} y={17.5} width={3} height={7.5} fill="#5e372e" />
        </svg>
      );
    default:
      return (
        <svg width={30} height={30} viewBox="0 0 30 30" aria-hidden="true">
          <rect x={4} y={25} width={22} height={2.5} rx={0.8} fill="#b6c7a3" />
          <rect x={6} y={15} width={18} height={10} fill="#d8c9b4" stroke="#8a7a5f" strokeWidth={1} />
          <path d="M4 16 L15 6 L26 16 Z" fill="#5a7086" stroke="#43566a" strokeWidth={1} strokeLinejoin="round" />
          <rect x={13} y={19} width={4} height={6} rx={0.8} fill="#7c6448" />
          <rect x={8} y={17.5} width={3} height={3} fill="#9dbfd3" />
          <rect x={19} y={17.5} width={3} height={3} fill="#9dbfd3" />
        </svg>
      );
  }
}

export function LogGlyph({
  icon,
}: {
  icon: "shear" | "bolt" | "frame" | "pulse";
}): JSX.Element {
  switch (icon) {
    case "shear":
      return (
        <svg width={18} height={18} viewBox="0 0 18 18" aria-hidden="true">
          <line x1={2.5} y1={6.2} x2={11} y2={6.2} stroke="#7f8790" strokeWidth={1.6} strokeLinecap="round" />
          <path d="M11 3.6 L15.5 6.2 L11 8.8 Z" fill="#7f8790" />
          <line x1={15.5} y1={11.8} x2={7} y2={11.8} stroke="#7f8790" strokeWidth={1.6} strokeLinecap="round" />
          <path d="M7 9.2 L2.5 11.8 L7 14.4 Z" fill="#7f8790" />
        </svg>
      );
    case "bolt":
      return (
        <svg width={18} height={18} viewBox="0 0 18 18" aria-hidden="true">
          <rect x={5.5} y={2} width={7} height={3.6} rx={0.8} fill="#9aa1a9" stroke="#6d757e" strokeWidth={1} />
          <rect x={7.4} y={5.6} width={3.2} height={10} fill="#aab1b8" stroke="#6d757e" strokeWidth={1} />
          <line x1={7.4} y1={8.2} x2={10.6} y2={8.2} stroke="#6d757e" strokeWidth={0.8} />
          <line x1={7.4} y1={10.2} x2={10.6} y2={10.2} stroke="#6d757e" strokeWidth={0.8} />
          <line x1={7.4} y1={12.2} x2={10.6} y2={12.2} stroke="#6d757e" strokeWidth={0.8} />
          <line x1={7.4} y1={14.2} x2={10.6} y2={14.2} stroke="#6d757e" strokeWidth={0.8} />
        </svg>
      );
    case "frame":
      return (
        <svg width={18} height={18} viewBox="0 0 18 18" aria-hidden="true">
          <rect x={3} y={2} width={3.5} height={14} fill="#9aa1a9" stroke="#6d757e" strokeWidth={1} />
          <rect x={6.5} y={6.5} width={9.5} height={3.6} fill="#aab1b8" stroke="#6d757e" strokeWidth={1} />
          <rect x={6.5} y={5.4} width={1.6} height={5.8} fill="#7f8790" />
          <circle cx={10.7} cy={8.3} r={0.9} fill="#6d757e" />
          <circle cx={13.7} cy={8.3} r={0.9} fill="#6d757e" />
        </svg>
      );
    case "pulse":
      return (
        <svg width={18} height={18} viewBox="0 0 18 18" aria-hidden="true">
          <polyline
            points="2,9 5,9 7,4 10,14 12,9 16,9"
            fill="none"
            stroke="#7f8790"
            strokeWidth={1.6}
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      );
  }
}
