// Eng am Text anliegende, weiche Abdunklung (Doktrin §5: Scrim nur textgroß).
// Statisch (kein animierter Blur); Deckkraft folgt dem Elternblock.
import React from "react";

export const Abdunklung: React.FC<{ staerke: number; randX?: number; randY?: number; weich?: number; style?: React.CSSProperties }> = ({
  staerke,
  randX = 26,
  randY = 10,
  weich = 16,
  style,
}) => (
  <div
    style={{
      position: "absolute",
      left: -randX,
      right: -randX,
      top: -randY,
      bottom: -randY,
      borderRadius: 40,
      background: `rgba(0,0,0,${staerke})`,
      filter: `blur(${weich}px)`,
      ...style,
    }}
  />
);
