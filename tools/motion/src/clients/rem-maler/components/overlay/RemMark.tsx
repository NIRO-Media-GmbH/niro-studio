// ============================================================
// REM Overlay — RemMark
// Original REM "R"-Monogramm als Vektor (Path + Verlauf 1:1 aus
// dem Favicon von rem-maler.de, viewBox 180×180). Skaliert
// verlustfrei — im Gegensatz zum 300px-Logo-Bitmap der Website.
// ============================================================

import React from "react";

interface RemMarkProps {
  size: number;
}

export const RemMark: React.FC<RemMarkProps> = ({ size }) => {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 180 180"
      xmlns="http://www.w3.org/2000/svg"
    >
      <defs>
        <linearGradient
          id="rem-mark-gradient"
          x1="17.157417"
          y1="36.322688"
          x2="152.629579"
          y2="165.477496"
          gradientUnits="userSpaceOnUse"
        >
          <stop offset="0" stopColor="#d63427" />
          <stop offset="0.239225" stopColor="#fcd8d9" />
          <stop offset="0.280548" stopColor="#f8c7c7" />
          <stop offset="0.36324" stopColor="#ee9c99" />
          <stop offset="0.478524" stopColor="#de574f" />
          <stop offset="0.537309" stopColor="#d63227" />
          <stop offset="0.581897" stopColor="#d7392e" />
          <stop offset="0.65098" stopColor="#db4e44" />
          <stop offset="0.735908" stopColor="#e27068" />
          <stop offset="0.833421" stopColor="#eb9f9a" />
          <stop offset="0.940135" stopColor="#f7dad8" />
          <stop offset="1" stopColor="#fff" />
        </linearGradient>
      </defs>
      <path
        fill="url(#rem-mark-gradient)"
        d="M126.138484,104.069134c4.627841-1.561515,8.687515-3.548823,12.169904-5.993597,9.603921-6.726967,14.405882-16.766226,14.405882-30.101894,0-11.62436-4.911925-20.953836-14.726657-27.996272-9.80556-7.034543-23.881548-10.551838-42.228022-10.551838h-23.148378v30.472574h24.538764c5.26022,0,9.200756,.851683,11.840011,2.570933,2.630082,1.711308,3.940536,4.589769,3.940536,8.627586,0,4.156034-1.310454,7.066071-3.940536,8.714323-2.639255,1.656098-6.579791,2.476253-11.840011,2.476253h-24.538764v28.090952h9.136545l24.889573,40.196315h53.967186l-34.466031-46.505334ZM19.395485,29.425532v121.148936h48.633694V29.425532H19.395485Z"
      />
    </svg>
  );
};
