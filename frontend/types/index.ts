export interface HealthStatusResponse {
  status: "healthy" | "unhealthy" | "degraded" | string;
  service: string;
  version: string;
  environment: string;
  database: string;
}

export interface NavigationItem {
  name: string;
  href: string;
  icon: string;
  badge?: string;
  active?: boolean;
}
