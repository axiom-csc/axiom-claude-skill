Output demo.gif

Set Shell "bash"
Set FontSize 14
Set Width 900
Set Height 450
Set Theme "Dracula"
Set Padding 20

Type "mkdir -p /tmp/axiom-demo && cd /tmp/axiom-demo && git init -q"
Enter
Sleep 400ms

Type "echo 'MAX_TRANSACTION = 10000' > checkout.py"
Enter
Sleep 300ms

Type "curl -fsSL https://raw.githubusercontent.com/axiom-csc/axiom-claude-skill/v1.2.2/install.sh | bash"
Enter
Sleep 8s

Type "cat > .axiom/invariants.yaml << 'EOF'"
Enter
Type "rules:"
Enter
Type "  - concept: transaction_value"
Enter
Type "    op: lte"
Enter
Type "    value: 10000"
Enter
Type "    action_on_fail: BLOCK"
Enter
Type "EOF"
Enter
Sleep 400ms

Type `echo '{"tool_name":"Edit","tool_input":{"file_path":"checkout.py","new_string":"MAX_TRANSACTION = $75,000"}}' | python3 .claude/skills/axiom-csc/hooks/pre_tool_use.py`
Enter
Sleep 1500ms

Sleep 1500ms

Type "cat checkout.py"
Enter
Sleep 500ms

Type "cd ~ && rm -rf /tmp/axiom-demo"
Enter
Sleep 300ms
