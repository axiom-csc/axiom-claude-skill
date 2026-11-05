# VHS tape for Axiom CSC demo
# Generate demo.gif: brew install charmbracelet/tap/vhs && vhs scripts/demo.tape
# Output: demo/demo.gif

Output demo/demo.gif

Set FontSize 14
Set Width 900
Set Height 420
Set Theme "Dracula"
Set Padding 20

# Start at a clean prompt in the repo root
Type "# Axiom CSC — Payment Limit Protection demo"
Enter
Sleep 500ms

# Show the invariants file
Type "cat .axiom/invariants.yaml"
Enter
Sleep 1s

# Scenario 1: DENY — raise MAX_TRANSACTION above limit
Type "# Scenario 1: agent tries to raise the payment limit above 50000"
Enter
Sleep 300ms
Type `echo '{"tool_name":"Edit","tool_input":{"file_path":"src/payments/checkout.py","new_string":"MAX_TRANSACTION = 75000"}}' | python3 .claude/skills/axiom-csc/hooks/pre_tool_use.py`
Enter
Sleep 2s

# Scenario 2: ALLOW — CSS change
Type "# Scenario 2: CSS style change — no invariants touched"
Enter
Sleep 300ms
Type `echo '{"tool_name":"Edit","tool_input":{"file_path":"src/static/main.css","new_string":"body { color: red; }"}}' | python3 .claude/skills/axiom-csc/hooks/pre_tool_use.py`
Enter
Sleep 2s

Type "# done"
Enter
Sleep 500ms
