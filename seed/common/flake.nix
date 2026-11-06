{
  description = "<<WORKSPACE_NAME>> work-memory workspace";

  inputs = {
    graft.url = "github:danielnaab/graft/v2.6.0";
    nixpkgs.follows = "graft/nixpkgs";
    meta-knowledge-base = {
      url = "github:danielnaab/meta-knowledge-base/v1.0.1";
      flake = false;
    };
    notebook-conventions = {
      url = "github:danielnaab/notebook-conventions/v0.1.3";
      flake = false;
    };
    knowledge-base-integrity = {
      url = "github:danielnaab/knowledge-base-integrity/v0.2.0";
      flake = false;
    };
  };

  outputs = inputs:
    let
      # The kit's flake wiring (dev shell, check apps, task check) comes from the pinned scion.
      # Before the first `nix run .#graft` the file does not exist yet; outputs are graft's only.
      wiring = ./.scions/notebook-conventions/nix/workspace.nix;
    in
    inputs.graft.lib.mkFlake {
      inherit inputs;
      # named, because knowledge-base-integrity is `flake = false` for the kit but isn't a scion
      scions = [ "meta-knowledge-base" "notebook-conventions" ];
      dir = ".scions";
      outputs = if builtins.pathExists wiring then import wiring { inherit inputs; } else { };
    };
}
