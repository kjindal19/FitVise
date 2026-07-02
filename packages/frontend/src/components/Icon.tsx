// Minimal inline icon set (stroke icons matching the design language).
type P = { size?: number; className?: string; stroke?: string };
const base = (size = 22, stroke = "currentColor") => ({
  width: size,
  height: size,
  viewBox: "0 0 24 24",
  fill: "none",
  stroke,
  strokeWidth: 1.9,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
});

export const HomeIcon = ({ size, stroke }: P) => (
  <svg {...base(size, stroke)}>
    <path d="M3 11l9-8 9 8M5 10v10h14V10" />
  </svg>
);
export const ProgrammeIcon = ({ size, stroke }: P) => (
  <svg {...base(size, stroke)}>
    <rect x="4" y="3" width="16" height="18" rx="2" />
    <path d="M8 8h8M8 12h8M8 16h5" />
  </svg>
);
export const ProgressIcon = ({ size, stroke }: P) => (
  <svg {...base(size, stroke)}>
    <path d="M3 17l5-5 4 4 7-8" />
  </svg>
);
export const JournalIcon = ({ size, stroke }: P) => (
  <svg {...base(size, stroke)}>
    <path d="M6 3h10l4 4v14H6z" />
    <path d="M9 9h7M9 13h7M9 17h4" />
  </svg>
);
export const PlusIcon = ({ size, stroke }: P) => (
  <svg {...base(size, stroke)}>
    <path d="M12 5v14M5 12h14" />
  </svg>
);
export const BellIcon = ({ size, stroke }: P) => (
  <svg {...base(size, stroke)}>
    <path d="M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9" />
    <path d="M13.7 21a2 2 0 0 1-3.4 0" />
  </svg>
);
export const CoachIcon = ({ size, stroke }: P) => (
  <svg {...base(size, stroke)}>
    <path d="M21 11.5a8.38 8.38 0 0 1-8.5 8.5 8.5 8.5 0 0 1-3.8-.9L3 21l1.9-5.7A8.38 8.38 0 0 1 4 11.5 8.5 8.5 0 0 1 12.5 3 8.38 8.38 0 0 1 21 11.5z" />
  </svg>
);
export const BackIcon = ({ size, stroke }: P) => (
  <svg {...base(size, stroke)} strokeWidth={2}>
    <path d="M15 18l-6-6 6-6" />
  </svg>
);
export const CheckIcon = ({ size, stroke }: P) => (
  <svg {...base(size, stroke)} strokeWidth={3}>
    <path d="M20 6L9 17l-5-5" />
  </svg>
);
export const FlameIcon = ({ size, stroke }: P) => (
  <svg {...base(size, stroke)}>
    <path d="M12 2s5 4.5 5 9a5 5 0 0 1-10 0c0-1.5.7-3 1.5-4C8 9 12 6 12 2z" />
  </svg>
);
export const CloseIcon = ({ size, stroke }: P) => (
  <svg {...base(size, stroke)} strokeWidth={2.2}>
    <path d="M18 6L6 18M6 6l12 12" />
  </svg>
);
export const PlusCircleIcon = ({ size, stroke }: P) => (
  <svg {...base(size, stroke)}>
    <circle cx="12" cy="12" r="9" />
    <path d="M12 8v8M8 12h8" />
  </svg>
);
export const MinusIcon = ({ size, stroke }: P) => (
  <svg {...base(size, stroke)} strokeWidth={2.2}>
    <path d="M5 12h14" />
  </svg>
);
