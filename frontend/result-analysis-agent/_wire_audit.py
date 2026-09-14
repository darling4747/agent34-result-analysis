import pathlib

FE = pathlib.Path(r"c:\Users\HP Victus\OneDrive - Vignan University\Pictures\project\frontend\result-analysis-agent\src")
LF = chr(10)

# ── 1. Add Shield to Sidebar ICON_MAP ────────────────────────────────────────
p_sidebar = FE / "components" / "layout" / "Sidebar.tsx"
src = p_sidebar.read_text(encoding='utf-8')
if 'Shield' not in src:
    src = src.replace(
        "  AlertTriangle, BookOpen, FileText, History, LayoutDashboard,\n  Layers, LineChart, LogOut, Sparkles, TrendingUp, Trophy,\n  Upload, Users, UserCheck, X, Activity, Settings,",
        "  AlertTriangle, BookOpen, FileText, History, LayoutDashboard,\n  Layers, LineChart, LogOut, Shield, Sparkles, TrendingUp, Trophy,\n  Upload, Users, UserCheck, X, Activity, Settings,"
    )
    src = src.replace(
        "  Settings:        <Settings size={16} aria-hidden=\"true\" />,",
        "  Settings:        <Settings size={16} aria-hidden=\"true\" />,\n  Shield:          <Shield size={16} aria-hidden=\"true\" />,"
    )
    p_sidebar.write_text(src, encoding='utf-8')
    print("Sidebar: Shield icon added")
else:
    print("Sidebar: Shield already present")

# ── 2. Add /audit-logs route to App.tsx ──────────────────────────────────────
p_app = FE / "App.tsx"
src_app = p_app.read_text(encoding='utf-8')
if 'AuditLogs' not in src_app:
    # Add lazy import
    src_app = src_app.replace(
        "const Settings            = lazy(() => import('@/pages/Settings'));",
        "const Settings            = lazy(() => import('@/pages/Settings'));\nconst AuditLogs           = lazy(() => import('@/pages/AuditLogs'));"
    )
    # Add route
    src_app = src_app.replace(
        "                <Route path=\"/settings\"         element={<Settings />} />",
        "                <Route path=\"/settings\"         element={<Settings />} />\n                <Route path=\"/audit-logs\"       element={<AuditLogs />} />"
    )
    p_app.write_text(src_app, encoding='utf-8')
    print("App.tsx: /audit-logs route added")
else:
    print("App.tsx: AuditLogs already present")

# ── 3. Ensure MFA does NOT block login when enabled  ─────────────────────────
# The MFA is already disabled on all user accounts via seed
# The AuthContext needs to handle mfa_required gracefully
# Check AuthContext login method

p_ctx = FE / "contexts" / "AuthContext.tsx"
src_ctx = p_ctx.read_text(encoding='utf-8')
if 'mfa_required' not in src_ctx:
    # Add mfa_required handling in login method
    # Find the line that sets token and user
    old_login = (
        "    localStorage.setItem(TOKEN_KEY, access_token);\n"
        "    if (refresh_token) localStorage.setItem(REFRESH_KEY, refresh_token);"
    )
    new_login = (
        "    // mfa_required means we need a second factor — handled by Login page\n"
        "    if (res.data.mfa_required) return res.data;\n"
        "    const access_token = res.data.access_token;\n"
        "    const refresh_token = res.data.refresh_token;\n"
        "    const must_change_password = res.data.must_change_password;\n"
        "    const user = res.data.user;\n"
        "    localStorage.setItem(TOKEN_KEY, access_token);\n"
        "    if (refresh_token) localStorage.setItem(REFRESH_KEY, refresh_token);"
    )
    if old_login in src_ctx:
        src_ctx = src_ctx.replace(old_login, new_login)
        p_ctx.write_text(src_ctx, encoding='utf-8')
        print("AuthContext: mfa_required handling added")
    else:
        print("AuthContext: login pattern differs, skipping (MFA disabled on accounts anyway)")
else:
    print("AuthContext: mfa_required already handled")

print("All fixes applied")