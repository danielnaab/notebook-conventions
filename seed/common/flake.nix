{
  description = "<<WORKSPACE_NAME>> work-memory workspace";

  inputs = {
    graft.url = "github:danielnaab/graft/v2.6.0";
    nixpkgs.follows = "graft/nixpkgs";
    meta-knowledge-base = {
      url = "github:danielnaab/meta-knowledge-base/v1.1.0";
      flake = false;
    };
    notebook-conventions = {
      url = "github:danielnaab/notebook-conventions/v0.2.0";
      flake = false;
    };
    knowledge-base-integrity = {
      url = "github:danielnaab/knowledge-base-integrity/v0.4.0";
      flake = false;
    };
  };

  outputs = inputs: inputs.graft.lib.mkFlake {
    inherit inputs;
    # named, because knowledge-base-integrity is `flake = false` for the kit but isn't a scion
    scions = [ "meta-knowledge-base" "notebook-conventions" ];
    dir = ".scions";
    # The kit's flake wiring (dev shell, check apps, task check), read from the pin itself so it is
    # there before the first `nix run .#graft`.
    outputs = import "${inputs.notebook-conventions}/nix/workspace.nix" { inherit inputs; };
  };
}
