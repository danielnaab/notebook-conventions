{
  description = "Conventions, tools, and a starter seed for Markdown work-memory workspaces";

  inputs = {
    graft.url = "github:danielnaab/graft/v2.5.1";
    nixpkgs.follows = "graft/nixpkgs";
    meta-knowledge-base = {
      url = "github:danielnaab/meta-knowledge-base/v1.0.1";
      flake = false;
    };
    knowledge-base-integrity = {
      url = "github:danielnaab/knowledge-base-integrity/v0.2.0";
      flake = false;
    };
  };

  outputs = inputs:
    let
      lib = inputs.nixpkgs.lib;
      systems = [ "aarch64-darwin" "x86_64-darwin" "aarch64-linux" "x86_64-linux" ];
      forAll = f: lib.genAttrs systems (system: f inputs.nixpkgs.legacyPackages.${system});
      graftOutputs = inputs.graft.lib.mkGraft {
        inherit inputs;
        deps = [ "meta-knowledge-base" ];
        dir = ".scions";
      };
      # The kit has no task records of its own, so it skips the task check.
      workspace = import ./nix/workspace.nix { inherit inputs; withTasks = false; };
      kitChecks = {
        checks = forAll (pkgs: {
          tests = pkgs.runCommand "kit-tests" {
            nativeBuildInputs = [ (pkgs.python3.withPackages (ps: [ ps.pyyaml ])) pkgs.git ];
            KBI_SRC = "${inputs.knowledge-base-integrity}/src";
            PYTHONDONTWRITEBYTECODE = "1";
          } ''
            cp -r ${inputs.self} src && chmod -R u+w src && cd src
            python -m unittest discover -s tests -v
            touch $out
          '';
        });
      };
    in lib.recursiveUpdate (lib.recursiveUpdate graftOutputs workspace) kitChecks;
}
