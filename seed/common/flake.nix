{
  description = "<<WORKSPACE_NAME>> work-memory workspace";

  inputs = {
    graft.url = "github:danielnaab/graft/v2.7.0";
    nixpkgs.follows = "graft/nixpkgs";
    # The conventions and the checker; the checker is read from this same pin (its src/).
    knowledge-base-kit = {
      url = "github:danielnaab/knowledge-base-kit/v2.0.0";
      flake = false;
    };
    notebook-kit = {
      url = "github:danielnaab/notebook-kit/v1.1.0";
      flake = false;
    };
  };

  outputs = inputs: inputs.graft.lib.mkFlake {
    inherit inputs;
    dir = ".scions";
    # The kit's flake wiring (dev shell, check apps, task check), read from the pin itself so it is
    # there before the first `nix run .#graft`.
    outputs = import "${inputs.notebook-kit}/nix/workspace.nix" { inherit inputs; };
  };
}
