{
  description = "Conventions, tools, and a starter seed for Markdown work-memory workspaces";

  inputs = {
    graft.url = "github:danielnaab/graft/v2.7.0";
    nixpkgs.follows = "graft/nixpkgs";
    # The conventions and the checker: grafted to .scions/, and the checker read from the same pin.
    knowledge-base-kit = {
      url = "github:danielnaab/knowledge-base-kit/v2.0.0";
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
            KBI_SRC = "${inputs.knowledge-base-kit}/src";
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
      dir = ".scions";
      outputs = lib.recursiveUpdate workspace kitChecks;
    };
}
