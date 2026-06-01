/** Noor — a friendly mascot in Western Grammar School colours: a sky-blue shield
 * with a red rim, navy face, a graduation cap and sun-yellow tassel. Blinking
 * eyes + smile like a study buddy. Pure SVG, no deps. Original stylised mascot
 * inspired by the WGS palette (not a reproduction of the school crest). */
export default function Mascot({
  size = 96,
  bob = false,
  className = "",
}: {
  size?: number;
  bob?: boolean;
  className?: string;
}) {
  const SKY = "#62C6EC";
  const RED = "#E5392E";
  const NAVY = "#222B79";
  const SUN = "#FDB81E";

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 120 120"
      fill="none"
      role="img"
      aria-label="Noor, the Western Grammar School study buddy"
      className={`${bob ? "animate-bob" : ""} ${className}`}
      style={{ transformOrigin: "center" }}
    >
      {/* light glints */}
      <circle cx="20" cy="46" r="3" fill={SUN} />
      <circle cx="100" cy="54" r="2.6" fill={SKY} />
      <circle cx="96" cy="86" r="2" fill={SUN} opacity="0.8" />

      {/* shadow */}
      <ellipse cx="60" cy="110" rx="28" ry="5" fill="rgba(34,43,121,0.12)" />

      {/* shield body */}
      <path
        d="M32 44 C32 39 35 38.5 39 38.5 L81 38.5 C85 38.5 88 39 88 44 L88 68 C88 84 75 95 60 101 C45 95 32 84 32 68 Z"
        fill="url(#shield)"
        stroke={RED}
        strokeWidth="4.5"
        strokeLinejoin="round"
      />
      {/* thin inner rim */}
      <path
        d="M37 46 C37 43 38.5 43 41 43 L79 43 C81.5 43 83 43 83 46 L83 67 C83 80 72 89 60 94 C48 89 37 80 37 67 Z"
        fill="none"
        stroke={NAVY}
        strokeWidth="1.4"
        opacity="0.5"
      />
      {/* sheen */}
      <ellipse cx="50" cy="56" rx="20" ry="14" fill="#ffffff" opacity="0.14" />

      {/* graduation cap */}
      <path d="M49 33 L71 33 L74 40 C67 42 53 42 46 40 Z" fill={NAVY} />
      <path d="M30 25 L60 16 L90 25 L60 34 Z" fill={NAVY} />
      <path d="M30 25 L60 16 L90 25 L60 34 Z" fill="#ffffff" opacity="0.12" />
      <circle cx="60" cy="25" r="2.6" fill={SUN} />
      <path d="M60 25 Q86 23 87 29 L88 47" stroke={SUN} strokeWidth="2.2" strokeLinecap="round" fill="none" />
      <circle cx="88" cy="49" r="3.2" fill={SUN} />

      {/* cheeks */}
      <circle cx="44" cy="71" r="5.5" fill={RED} opacity="0.5" />
      <circle cx="76" cy="71" r="5.5" fill={RED} opacity="0.5" />

      {/* eyes */}
      <g className="animate-blink" style={{ transformOrigin: "center" }}>
        <circle cx="48" cy="61" r="6.5" fill={NAVY} />
        <circle cx="72" cy="61" r="6.5" fill={NAVY} />
        <circle cx="50" cy="59" r="2" fill="#ffffff" />
        <circle cx="74" cy="59" r="2" fill="#ffffff" />
      </g>

      {/* smile */}
      <path d="M50 77 Q60 85 70 77" stroke={NAVY} strokeWidth="3.5" strokeLinecap="round" fill="none" />

      <defs>
        <linearGradient id="shield" x1="60" y1="38" x2="60" y2="101" gradientUnits="userSpaceOnUse">
          <stop stopColor="#7FD2F2" />
          <stop offset="1" stopColor={SKY} />
        </linearGradient>
      </defs>
    </svg>
  );
}
