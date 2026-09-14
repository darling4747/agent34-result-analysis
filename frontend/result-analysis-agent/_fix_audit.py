import pathlib

FE = pathlib.Path(r"c:\Users\HP Victus\OneDrive - Vignan University\Pictures\project\frontend\result-analysis-agent\src")
LF = chr(10)
BT = chr(96)
DOLLAR = chr(36)

p = FE / "pages" / "AuditLogs.tsx"
lines = p.read_text(encoding='utf-8').splitlines()

new_lines = []
for line in lines:
    # Find the corrupted className line at line 39
    if 'className={inline-flex items-center' in line and BT not in line:
        # The template literal backtick was stripped
        # The correct line should be: className={inline-flex...}
        new_lines.append(
            "      const cls = ACTION_COLOR[r.action] ?? 'text-gray-700 bg-gray-50 border-gray-200';" + LF +
            "      return (" + LF +
            "        <span className={" + BT + "inline-flex items-center px-2 py-0.5 text-xs font-medium rounded-full border " + DOLLAR + "{cls}" + BT + "}>" + LF +
            "          {r.action.replace(/_/g, ' ')}" + LF +
            "        </span>" + LF +
            "      );"
        )
        # Skip the next lines that were part of the old corrupted block
    else:
        new_lines.append(line)

p.write_text(LF.join(new_lines), encoding='utf-8')
print("Fixed AuditLogs.tsx template literal")

# Verify
check = p.read_text(encoding='utf-8')
print("Has backtick className:", BT + "inline-flex" in check)
print("Line count:", len(check.splitlines()))