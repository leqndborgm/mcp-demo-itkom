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
          ];
          shellHook = ''
            export LD_LIBRARY_PATH="${pkgs.lib.makeLibraryPath [
              pkgs.stdenv.cc.cc.lib
              pkgs.zlib # zlib is also very commonly required by numpy/pandas wheels
            ]}:$LD_LIBRARY_PATH"  
            echo ""
            echo "╔══════════════════════════════════════════════╗"
            echo "║   MCP Server Development Shell               ║"
            echo "╠══════════════════════════════════════════════╣"
            echo "║  FastMCP server is ready to use              ║"
            echo "╚══════════════════════════════════════════════╝"
            echo ""
          '';
        };
      });
}
