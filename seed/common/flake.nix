{
  description = "<<WORKSPACE_NAME>> work-memory workspace";

  # The scions in .scions/ (notebook-kit, knowledge-base-kit) are git submodules; each wires its own tools, apps
  # and checks into this flake (its graft.nix). Settings for the kit's tools are in notebook-kit.yaml.
  inputs.self.submodules = true;
  inputs.graft.url = "github:danielnaab/graft/v2.13.1";

  outputs = inputs: inputs.graft.lib.mkFlake {
    inherit inputs;
    dir = ".scions";
  };
}
