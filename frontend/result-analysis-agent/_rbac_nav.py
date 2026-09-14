import pathlib

FE = pathlib.Path(r"c:\Users\HP Victus\OneDrive - Vignan University\Pictures\project\frontend\result-analysis-agent\src")
LF = chr(10)

# ── 1. Add getVisibleNavItems to constants.ts ─────────────────────────────────
p = FE / "utils" / "constants.ts"
src = p.read_text(encoding='utf-8')

# Add role-based visibility AFTER NAV_ITEMS if not already present
if 'getVisibleNavItems' not in src:
    visibility_code = '''
// ─── Role-based navigation visibility ────────────────────────────────────────
// Paths hidden for each role (not visible = not rendered, not just disabled)

const HIDDEN_PATHS_BY_ROLE: Record<string, string[]> = {
  PLATFORM_ADMIN: [],  // sees everything
  DEAN: ['/upload', '/users', '/settings', '/audit-logs'],
  HOD: ['/upload', '/users', '/settings', '/audit-logs'],
  FACULTY: ['/upload', '/import-history', '/faculty', '/users', '/settings', '/audit-logs'],
  IQAC: ['/upload', '/users', '/settings', '/audit-logs'],
  MANAGEMENT: ['/upload', '/users', '/settings', '/audit-logs'],
  AUDITOR: ['/upload', '/users', '/settings'],
};

export function getVisibleNavItems(role?: string): typeof NAV_ITEMS[number][] {
  if (!role) return [];
  const hidden = HIDDEN_PATHS_BY_ROLE[role] ?? [];
  return NAV_ITEMS.filter((item) => !hidden.includes(item.path)) as typeof NAV_ITEMS[number][];
}
'''
    src += visibility_code
    p.write_text(src, encoding='utf-8')
    print("constants.ts: getVisibleNavItems added")
else:
    print("constants.ts: getVisibleNavItems already present")

# ── 2. Update Sidebar.tsx to use getVisibleNavItems ───────────────────────────
ps = FE / "components" / "layout" / "Sidebar.tsx"
ssrc = ps.read_text(encoding='utf-8')

if 'getVisibleNavItems' not in ssrc:
    # Add import
    ssrc = ssrc.replace(
        "import { NAV_ITEMS } from '@/utils/constants';",
        "import { getVisibleNavItems } from '@/utils/constants';"
    )
    # Replace NAV_ITEMS.map with filtered version
    ssrc = ssrc.replace(
        "          <ul role=\"list\" className=\"flex flex-col gap-0.5 px-2\">\n            {NAV_ITEMS.map((item) => {",
        "          <ul role=\"list\" className=\"flex flex-col gap-0.5 px-2\">\n            {getVisibleNavItems(user?.role).map((item) => {"
    )
    ps.write_text(ssrc, encoding='utf-8')
    print("Sidebar.tsx: role-based nav filtering applied")
else:
    print("Sidebar.tsx: already uses getVisibleNavItems")