/** Noor — a friendly geometric open-book buddy. Pure SVG, no deps. */
export default function Mascot({
  size = 96,
  bob = false,
  className = "",
}: {
  size?: number;
  bob?: boolean;
  className?: string;
}) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 120 120"
      fill="none"
      role="img"
      aria-label="Noor the textbook buddy"
      className={`${bob ? "animate-bob" : ""} ${className}`}
      style={{ transformOrigin: "center" }}
    >
      {/* shadow */}
      <ellipse cx="60" cy="108" rx="34" ry="6" fill="rgba(43,42,38,0.10)" />
      {/* body / book */}
      <rect x="20" y="26" width="80" height="68" rx="18" fill="var(--color-teal)" />
      <rect x="20" y="26" width="80" height="68" rx="18" fill="url(#sheen)" opacity="0.18" />
      {/* spine pages */}
      <path d="M60 30 V90" stroke="var(--color-paper)" strokeWidth="3" strokeLinecap="round" opacity="0.55" />
      {/* cheeks */}
      <circle cx="40" cy="68" r="6" fill="var(--color-coral)" opacity="0.85" />
      <circle cx="80" cy="68" r="6" fill="var(--color-coral)" opacity="0.85" />
      {/* eyes */}
      <g className="animate-blink" style={{ transformOrigin: "center" }}>
        <circle cx="44" cy="54" r="6.5" fill="var(--color-ink)" />
        <circle cx="76" cy="54" r="6.5" fill="var(--color-ink)" />
        <circle cx="46" cy="52" r="2" fill="var(--color-paper)" />
        <circle cx="78" cy="52" r="2" fill="var(--color-paper)" />
      </g>
      {/* smile */}
      <path d="M50 74 Q60 82 70 74" stroke="var(--color-ink)" strokeWidth="3.5" strokeLinecap="round" fill="none" />
      {/* antenna with a friendly spark-of-an-idea sparkle */}
      <line x1="60" y1="26" x2="60" y2="16" stroke="var(--color-sun)" strokeWidth="3.5" strokeLinecap="round" />
      <path
        d="M60 3 L62.2 9.2 L68 11 L62.2 12.8 L60 19 L57.8 12.8 L52 11 L57.8 9.2 Z"
        fill="var(--color-sun)"
      />
      <defs>
        <linearGradient id="sheen" x1="20" y1="26" x2="100" y2="94" gradientUnits="userSpaceOnUse">
          <stop stopColor="#ffffff" />
          <stop offset="1" stopColor="#ffffff" stopOpacity="0" />
        </linearGradient>
      </defs>
    </svg>
  );
}
