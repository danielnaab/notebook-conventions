{
  description = "Conventions, tools, and a starter seed for Markdown work-memory workspaces";

  inputs = {
    graft.url = "github:danielnaab/graft/v2.6.0";
    nixpkgs.follows = "graft/nixpkgs";
    meta-knowledge-base = {
      url = "github:danielnaab/meta-knowledge-base/v1.1.0";
      flake = false;
    };
    knowledge-base-integrity = {
      url = "github:danielnaab/knowledge-base-integrity/v0.4.0";
      flake = false;
    };
  };

  outputs = inputs:
    let
      lib = inputs.nixpkgs.lib;
      systems = [ "aarch64-darwin" "x86_64-darwin" "aarch64-linux" "x86_64-linux" ];
      forAll = f: lib.genAttrs systems (system: f inputs.nixpkgs.legacyPackages.${system});
      # The kit has no task records of its own, so it skips the task check.
      workspace = import ./nix/workspace.nix { inherit inputs; withTasks = false; };
      kitChecks = {
        checks = forAll (pkgs: {
          tests = pkgs.runCommand "kit-tests" {
            nativeBuildInputs = [ (pkgs.python3.withPackages (ps: [ ps.pyyaml ])) pkgs.git pkgs.just ];
            KBI_SRC = "${inputs.knowledge-base-integrity}/src";
            PYTHONDONTWRITEBYTECODE = "1";
          } ''
            cp -r ${inputs.self} src && chmod -R u+w src && cd src
            python -m unittest discover -s tests -v
            touch $out
          '';
        });
      };
    in
    inputs.graft.lib.mkFlake {
      inherit inputs;
      # named, because knowledge-base-integrity is `flake = false` for the tools but isn't a scion
      scions = [ "meta-knowledge-base" ];
      dir = ".scions";
      outputs = lib.recursiveUpdate workspace kitChecks;
    };
}
