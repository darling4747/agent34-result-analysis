/**
 * Strict Centralized RBAC Specification & Page Visibility Registry
 * Agent 34 — Academic Result Analysis System
 */

export interface PageDefinition {
  path: string;
  label: string;
  icon: string;
  section: 'OVERVIEW' | 'RESULTS' | 'ANALYTICS' | 'INTELLIGENCE' | 'REPORTING' | 'ADMINISTRATION';
  permission?: string;
  allowedRoles: string[];
}

export const ROLE_PAGE_REGISTRY: PageDefinition[] = [
  {
    path: '/dashboard',
    label: 'Overview',
    icon: 'LayoutDashboard',
    section: 'OVERVIEW',
    allowedRoles: ['PLATFORM_ADMIN', 'DEAN', 'HOD', 'FACULTY', 'IQAC', 'MANAGEMENT', 'AUDITOR'],
  },
  {
    path: '/upload',
    label: 'Upload Results',
    icon: 'Upload',
    section: 'RESULTS',
    permission: 'RESULT_UPLOAD',
    allowedRoles: ['PLATFORM_ADMIN'],
  },
  {
    path: '/import-history',
    label: 'Import History',
    icon: 'History',
    section: 'RESULTS',
    permission: 'RESULT_READ',
    allowedRoles: ['PLATFORM_ADMIN', 'DEAN', 'HOD', 'IQAC', 'MANAGEMENT', 'AUDITOR'],
  },
  {
    path: '/courses',
    label: 'Course Analysis',
    icon: 'BookOpen',
    section: 'ANALYTICS',
    permission: 'ANALYSIS_COURSE',
    allowedRoles: ['PLATFORM_ADMIN', 'DEAN', 'HOD', 'FACULTY', 'IQAC', 'MANAGEMENT', 'AUDITOR'],
  },
  {
    path: '/sections',
    label: 'Section Analysis',
    icon: 'Layers',
    section: 'ANALYTICS',
    permission: 'ANALYSIS_SECTION',
    allowedRoles: ['PLATFORM_ADMIN', 'DEAN', 'HOD', 'FACULTY', 'IQAC', 'MANAGEMENT', 'AUDITOR'],
  },
  {
    path: '/faculty',
    label: 'Faculty Analysis',
    icon: 'Users',
    section: 'ANALYTICS',
    permission: 'ANALYSIS_FACULTY',
    allowedRoles: ['PLATFORM_ADMIN', 'DEAN', 'HOD', 'IQAC', 'AUDITOR'],
  },
  {
    path: '/merit-list',
    label: 'Merit List',
    icon: 'Trophy',
    section: 'ANALYTICS',
    permission: 'MERIT_READ',
    allowedRoles: ['PLATFORM_ADMIN', 'DEAN', 'HOD', 'FACULTY', 'IQAC', 'MANAGEMENT', 'AUDITOR'],
  },
  {
    path: '/correlation',
    label: 'Internal vs External',
    icon: 'TrendingUp',
    section: 'ANALYTICS',
    permission: 'CORRELATION_READ',
    allowedRoles: ['PLATFORM_ADMIN', 'DEAN', 'HOD', 'FACULTY', 'IQAC', 'MANAGEMENT', 'AUDITOR'],
  },
  {
    path: '/historical',
    label: 'Historical Trends',
    icon: 'LineChart',
    section: 'ANALYTICS',
    permission: 'HISTORICAL_READ',
    allowedRoles: ['PLATFORM_ADMIN', 'DEAN', 'HOD', 'FACULTY', 'IQAC', 'MANAGEMENT', 'AUDITOR'],
  },
  {
    path: '/interventions',
    label: 'Interventions',
    icon: 'AlertTriangle',
    section: 'ANALYTICS',
    permission: 'INTERVENTION_READ',
    allowedRoles: ['PLATFORM_ADMIN', 'DEAN', 'HOD', 'FACULTY', 'IQAC', 'MANAGEMENT', 'AUDITOR'],
  },
  {
    path: '/ai-insights',
    label: 'AI Insights',
    icon: 'Sparkles',
    section: 'INTELLIGENCE',
    allowedRoles: ['PLATFORM_ADMIN', 'DEAN', 'HOD', 'FACULTY', 'IQAC', 'MANAGEMENT', 'AUDITOR'],
  },
  {
    path: '/reports',
    label: 'Reports',
    icon: 'FileText',
    section: 'REPORTING',
    permission: 'REPORT_READ',
    allowedRoles: ['PLATFORM_ADMIN', 'DEAN', 'HOD', 'FACULTY', 'IQAC', 'MANAGEMENT', 'AUDITOR'],
  },
  {
    path: '/users',
    label: 'User Management',
    icon: 'UserCheck',
    section: 'ADMINISTRATION',
    permission: 'USER_READ',
    allowedRoles: ['PLATFORM_ADMIN'],
  },
  {
    path: '/settings',
    label: 'System Configuration',
    icon: 'Settings',
    section: 'ADMINISTRATION',
    permission: 'CONFIG_MANAGE',
    allowedRoles: ['PLATFORM_ADMIN'],
  },
  {
    path: '/audit-logs',
    label: 'Audit Logs',
    icon: 'Shield',
    section: 'ADMINISTRATION',
    permission: 'AUDIT_READ',
    allowedRoles: ['PLATFORM_ADMIN', 'AUDITOR'],
  },
];

/**
 * Returns true if the user's role is authorized to access the specified path.
 */
export function canAccessPage(role: string | undefined | null, path: string): boolean {
  if (!role) return false;
  const baseRoute = '/' + (path.split('/')[1] || '');
  const page = ROLE_PAGE_REGISTRY.find((p) => p.path === baseRoute || p.path === path);
  if (!page) return true;
  return page.allowedRoles.includes(role.toUpperCase());
}

/**
 * Returns only the pages physically visible to the user's role.
 * Contains ZERO unauthorized items, ZERO disabled placeholders.
 */
export function getVisiblePages(role: string | undefined | null): PageDefinition[] {
  if (!role) return [];
  const normalizedRole = role.toUpperCase();
  return ROLE_PAGE_REGISTRY.filter((page) => page.allowedRoles.includes(normalizedRole));
}

/**
 * Returns visible page items grouped by section headers.
 * Empty sections (sections with 0 items) are completely omitted.
 */
export function getVisibleNavigationSections(role: string | undefined | null) {
  const visiblePages = getVisiblePages(role);
  const sectionsMap = new Map<string, PageDefinition[]>();

  for (const page of visiblePages) {
    if (!sectionsMap.has(page.section)) {
      sectionsMap.set(page.section, []);
    }
    sectionsMap.get(page.section)!.push(page);
  }

  const result: { title: string; items: PageDefinition[] }[] = [];
  const sectionOrder: ('OVERVIEW' | 'RESULTS' | 'ANALYTICS' | 'INTELLIGENCE' | 'REPORTING' | 'ADMINISTRATION')[] = [
    'OVERVIEW',
    'RESULTS',
    'ANALYTICS',
    'INTELLIGENCE',
    'REPORTING',
    'ADMINISTRATION',
  ];

  for (const sectionKey of sectionOrder) {
    const items = sectionsMap.get(sectionKey);
    if (items && items.length > 0) {
      result.push({
        title: sectionKey,
        items,
      });
    }
  }

  return result;
}

/**
 * Check if the user is an Auditor (read-only role).
 */
export function isAuditor(role: string | undefined | null): boolean {
  return role?.toUpperCase() === 'AUDITOR';
}
