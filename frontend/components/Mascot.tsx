/** Noor — a friendly glowing book-buddy. Pure SVG, no deps.
 * Deliberately avoids any antenna / vertical+horizontal shapes that could read
 * as a cross. "Noor" means light, so it sits in a soft halo with round glints. */
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
      {/* soft light halo */}
      <circle cx="60" cy="58" r="46" fill="var(--color-sun)" opacity="0.16" />

      {/* scattered round light-glints (asymmetric, never a cross) */}
      <circle cx="99" cy="30" r="4.5" fill="var(--color-sun)" />
      <circle cx="22" cy="44" r="3" fill="var(--color-sun)" />
      <circle cx="96" cy="84" r="2.6" fill="var(--color-sun)" opacity="0.8" />
      <circle cx="30" cy="86" r="2" fill="var(--color-coral)" opacity="0.7" />

      {/* shadow */}
      <ellipse cx="60" cy="106" rx="32" ry="5.5" fill="rgba(43,42,38,0.10)" />

      {/* body */}
      <rect x="26" y="30" width="68" height="62" rx="22" fill="var(--color-teal)" />
      <rect x="26" y="30" width="68" height="62" rx="22" fill="url(#sheen)" opacity="0.18" />

      {/* a cheerful little curl on top (off-centre, organic — not an antenna) */}
      <path
        d="M64 31 C64 22 73 22 72 29"
        stroke="var(--color-sun)"
        strokeWidth="3.5"
        strokeLinecap="round"
        fill="none"
      />

      {/* cheeks */}
      <circle cx="42" cy="68" r="6" fill="var(--color-coral)" opacity="0.85" />
      <circle cx="78" cy="68" r="6" fill="var(--color-coral)" opacity="0.85" />

      {/* eyes */}
      <g className="animate-blink" style={{ transformOrigin: "center" }}>
        <circle cx="46" cy="56" r="6.5" fill="var(--color-ink)" />
        <circle cx="74" cy="56" r="6.5" fill="var(--color-ink)" />
        <circle cx="48" cy="54" r="2" fill="var(--color-paper)" />
        <circle cx="76" cy="54" r="2" fill="var(--color-paper)" />
      </g>

      {/* smile */}
      <path
        d="M50 74 Q60 82 70 74"
        stroke="var(--color-ink)"
        strokeWidth="3.5"
        strokeLinecap="round"
        fill="none"
      />

      <defs>
        <linearGradient id="sheen" x1="26" y1="30" x2="94" y2="92" gradientUnits="userSpaceOnUse">
          <stop stopColor="#ffffff" />
          <stop offset="1" stopColor="#ffffff" stopOpacity="0" />
        </linearGradient>
      </defs>
    </svg>
  );
}
