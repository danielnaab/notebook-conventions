{
  description = "<<WORKSPACE_NAME>> work-memory workspace";

  inputs = {
    graft.url = "github:danielnaab/graft/v2.5.1";
    nixpkgs.follows = "graft/nixpkgs";
    meta-knowledge-base = {
      url = "github:danielnaab/meta-knowledge-base/v1.0.1";
      flake = false;
    };
    notebook-conventions = {
      url = "github:danielnaab/notebook-conventions/v0.1.0";
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
      graftOutputs = inputs.graft.lib.mkGraft {
        inherit inputs;
        deps = [ "meta-knowledge-base" "notebook-conventions" ];
        dir = ".scions";
      };
      # The kit's flake wiring (dev shell, check apps, task check) comes from the pinned scion.
      # Before the first `nix run .#graft` the file does not exist yet; outputs are graft's only.
      wiring = ./.scions/notebook-conventions/nix/workspace.nix;
      workspace = if builtins.pathExists wiring then import wiring { inherit inputs; } else { };
    in lib.recursiveUpdate graftOutputs workspace;
}
