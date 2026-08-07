export default function Logo({ size = 28 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect width="32" height="32" rx="9" fill="url(#logo-gradient)" />
      <path
        d="M10 17.5 14 21.5 22 11.5" stroke="white" strokeWidth="2.4"
        strokeLinecap="round" strokeLinejoin="round"
      />
      <defs>
        <linearGradient id="logo-gradient" x1="0" y1="0" x2="32" y2="32" gradientUnits="userSpaceOnUse">
          <stop stopColor="#6d7bff" />
          <stop offset="1" stopColor="#4c56e0" />
        </linearGradient>
      </defs>
    </svg>
  );
}
