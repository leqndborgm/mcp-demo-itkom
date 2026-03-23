{
  description = "QSC MCP Server - Development Environment";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};

        mkScript = name: text:
          pkgs.writeShellScriptBin name ''
            set -euo pipefail
            ${text}
          '';
      in
      {
        # nix develop
        devShells.default = pkgs.mkShell {
          name = "mcp-server-dev";
          buildInputs = [
            pkgs.python313
            pkgs.python313Packages.fastmcp
            pkgs.python313Packages.pip
            pkgs.python313Packages.cyclopts
            pkgs.python313Packages.requests
            pkgs.psmisc # provides fuser
            (mkScript "mcp-server" ''
              # Cleanup port 8001
              fuser -k 8001/tcp 2>/dev/null || true
              
              echo "🚀 Starting MCP Server on http://localhost:8001..."
              python server.py http
            '')
            
            (mkScript "mcp-inspector" ''
              # Cleanup port 6274/6277 (client/proxy default ports for Inspector)
              fuser -k 6274/tcp 2>/dev/null || true
              fuser -k 6277/tcp 2>/dev/null || true
              
              if [ $# -eq 0 ]; then
                echo "🔍 No arguments provided. Defaulting to local MCP Server at http://localhost:8001/mcp"
                echo "   (You can pass your own args: e.g. 'mcp-inspector node build/index.js')"
                npx @modelcontextprotocol/inspector http://localhost:8001/mcp
              else
                echo "🔍 Running inspector globally for: $@"
                npx @modelcontextprotocol/inspector "$@"
              fi
            '')

            (mkScript "mcp-start" ''
              # Convenience script to start both local server and inspector
              echo "🚀 Starting both Server and Inspector..."
              mcp-server &
              SERVER_PID=$!
              
              sleep 2
              mcp-inspector &
              INSPECTOR_PID=$!
              
              trap "kill $SERVER_PID $INSPECTOR_PID 2>/dev/null" EXIT
              wait
            '')
          ];
          shellHook = ''
            export LD_LIBRARY_PATH="${pkgs.lib.makeLibraryPath [
              pkgs.stdenv.cc.cc.lib
              pkgs.zlib 
            ]}:$LD_LIBRARY_PATH"  
            
            # Cleanup port 8001
            echo "Cleaning up port 8001..."
            fuser -k 8001/tcp 2>/dev/null || true

            if [ ! -d .venv ]; then
              echo "Creating virtual environment..."
              python -m venv .venv
            fi
            source .venv/bin/activate
            
            # Install mcp-ui-server if not present
            if ! python -c "import mcp_ui_server" 2>/dev/null; then
              echo "Installing mcp-ui-server..."
              pip install mcp-ui-server
            fi

            echo ""
            echo "╔══════════════════════════════════════════════╗"
            echo "║   MCP Server Development Shell               ║"
            echo "╠══════════════════════════════════════════════╣"
            echo "║  Standard MCP-UI (MCP Apps) Ready            ║"
            echo "║  Commands:                                   ║"
            echo "║    mcp-server    - Run only Backend          ║"
            echo "║    mcp-inspector - Run independent Inspector ║"
            echo "║    mcp-start     - Run both together         ║"
            echo "╚══════════════════════════════════════════════╝"
            echo ""
          '';
        };
      });
}
