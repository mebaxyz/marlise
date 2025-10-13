#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 2 ]; then
    echo "Usage: $0 find|list <port>"
    echo "  find <port>  - exit 0 if connections for <port> exist, non-zero otherwise"
    echo "  list <port>  - print jack_lsp output for the port"
    exit 2
fi

cmd=$1
port=$2

if ! command -v jack_lsp >/dev/null 2>&1; then
    echo "jack_lsp not available" >&2
    exit 3
fi

if [ "$cmd" = "list" ]; then
    jack_lsp -c "$port" || true
    exit 0
elif [ "$cmd" = "find" ]; then
    out=$(jack_lsp -c "$port" 2>/dev/null || true)
    if [ -n "$out" ]; then
        echo "$out"
        exit 0
    else
        exit 1
    fi
else
    echo "Unknown command: $cmd" >&2
    exit 2
fi
