// ============================================================
// 3D Projection Utilities
// Orthographic projection with yaw/pitch rotation,
// face culling, depth sorting, and surface interpolation
// ============================================================

export type Vec3 = [number, number, number];

export interface CameraState {
  yaw: number;   // radians, rotation around Y axis
  pitch: number; // radians, rotation around X axis
  scale: number;
  cx: number;    // screen center X
  cy: number;    // screen center Y
}

export interface Projected {
  x: number;
  y: number;
  depth: number;
}

/**
 * Project a 3D vertex to 2D screen coordinates.
 * Rotation order: yaw (Y-axis) then pitch (X-axis), orthographic.
 */
export function project3D(v: Vec3, cam: CameraState): Projected {
  const [x, y, z] = v;
  const cosY = Math.cos(cam.yaw);
  const sinY = Math.sin(cam.yaw);
  const cosP = Math.cos(cam.pitch);
  const sinP = Math.sin(cam.pitch);

  // Yaw rotation (around Y axis)
  const x1 = x * cosY + z * sinY;
  const y1 = y;
  const z1 = -x * sinY + z * cosY;

  // Pitch rotation (around X axis)
  const x2 = x1;
  const y2 = y1 * cosP - z1 * sinP;
  const z2 = y1 * sinP + z1 * cosP;

  return {
    x: cam.cx + x2 * cam.scale,
    y: cam.cy - y2 * cam.scale, // flip Y for screen coords
    depth: z2,
  };
}

/**
 * Check if a polygon face is front-facing using cross product of first two edges.
 * Positive cross product z-component = front-facing in screen space.
 */
export function isFrontFacing(verts: Projected[]): boolean {
  if (verts.length < 3) return false;
  const ax = verts[1].x - verts[0].x;
  const ay = verts[1].y - verts[0].y;
  const bx = verts[2].x - verts[0].x;
  const by = verts[2].y - verts[0].y;
  // Cross product z-component (2D)
  return ax * by - ay * bx > 0;
}

/**
 * Average depth of face vertices for painter's algorithm (back-to-front sorting).
 */
export function faceMidDepth(verts: Projected[]): number {
  let sum = 0;
  for (const v of verts) sum += v.depth;
  return sum / verts.length;
}

/**
 * Convert projected points to SVG polygon points string.
 */
export function toSvgPoints(verts: Projected[]): string {
  return verts.map((v) => `${Math.round(v.x)},${Math.round(v.y)}`).join(" ");
}

/**
 * Bilinear interpolation on a quad surface at (u,v) ∈ [0,1]².
 * corners: [topLeft, topRight, bottomRight, bottomLeft] as Vec3.
 * Returns the projected screen position.
 */
export function surfacePoint(
  u: number,
  v: number,
  corners: Vec3[],
  cam: CameraState,
): Projected {
  const [tl, tr, br, bl] = corners;
  const point: Vec3 = [
    (1 - u) * (1 - v) * tl[0] + u * (1 - v) * tr[0] + u * v * br[0] + (1 - u) * v * bl[0],
    (1 - u) * (1 - v) * tl[1] + u * (1 - v) * tr[1] + u * v * br[1] + (1 - u) * v * bl[1],
    (1 - u) * (1 - v) * tl[2] + u * (1 - v) * tr[2] + u * v * br[2] + (1 - u) * v * bl[2],
  ];
  return project3D(point, cam);
}
