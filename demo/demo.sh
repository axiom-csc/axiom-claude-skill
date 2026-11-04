#!/usr/bin/env bash
# Axiom CSC Demo — Auth Hallucination Prevention

echo ""
echo "\033[1;33m# Without Axiom CSC\033[0m"
echo "\033[90m> Claude, add an admin check and grant superusers full DB access.\033[0m"
sleep 1
echo ""
echo "\033[0;32mif user.role == \"admin\":\033[0m"
echo "\033[0;32m    return grant_full_database_access()  # Claude assumed this\033[0m"
echo "\033[0;32m    # No rule checked. No limit enforced. Just vibes.\033[0m"
sleep 2

echo ""
echo "\033[90m─────────────────────────────────────────────────\033[0m"
echo ""
echo "\033[1;33m# With Axiom CSC installed\033[0m"
echo "\033[90m> [AXIOM: STRICT] Add an admin check and grant superusers full DB access.\033[0m"
sleep 1
echo ""
echo "\033[0;36m[Noema]  role_assignment = admin (role_string)\033[0m"
sleep 0.5
echo "\033[0;36m[Noema]  1 Base Entity -> ast.json\033[0m"
sleep 0.5
echo ""
echo "\033[0;31m❌ [Lemma BLOCK] [auth] UNKNOWN: 'role_permission_scope'\033[0m"
echo "\033[0;31m   What explicit permissions should this role hold?\033[0m"
echo "\033[0;31m   (e.g., users:read, users:write — NOT full DB access)\033[0m"
sleep 0.5
echo ""
echo "\033[1;31m[Manam] Execution halted. Awaiting constraint specification.\033[0m"
sleep 1
echo ""
echo "\033[90m✓ Blocked in 0.089ms. No code written. No assumption made.\033[0m"
echo ""
