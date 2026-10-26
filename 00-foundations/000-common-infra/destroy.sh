#!/bin/bash
# destroy.sh — 000-common-infra
# WARNING: Only run this after ALL other guide stacks have been destroyed.
# Deleting the shared IAM roles while guides are deployed will break them.
set -euo pipefail

# Silence JSII warning about untested Node.js version — cosmetic, not an error
export JSII_SILENCE_WARNING_UNTESTED_NODE_VERSION=1


STACK="AgentsOnAwsCommonInfra"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo ""
echo "=== WARNING ==="
echo ""
echo "This will DELETE the shared IAM roles and SSM parameters"
echo "used by ALL 66 guides."
echo ""
echo "Only do this if you have already run 'bash destroy.sh' in"
echo "every guide you deployed. Otherwise those stacks will break."
echo ""
read -p "Are you sure? Type 'yes' to confirm: " confirm
[ "$confirm" = "yes" ] || { echo "Aborted."; exit 0; }

cd "$SCRIPT_DIR/Infra"
cdk destroy "$STACK" --force

echo ""
echo "Common infra destroyed."
