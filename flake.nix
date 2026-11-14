{
  description = "Conventions, tools, and a starter seed for Markdown work-memory workspaces";

  # .scions/knowledge-base-kit is a git submodule (graft v2.13.0)
  inputs.self.submodules = true;
  inputs = {
    graft.url = "github:danielnaab/graft/v2.13.0";
    nixpkgs.follows = "graft/nixpkgs";
  };

  outputs = { self, graft, ... }@inputs:
    graft.lib.mkFlake {
      inherit inputs;
      dir = ".scions";
      # The kit's tools, apps and packages come from graft.nix, exactly as a workspace that grafts the kit gets
      # them, so they are defined once. The kit has no notebook-kit.yaml (no task records), so no task check.
      perSystem = { pkgs, lib, system, scions, ... }:
        let
          kit = consumer: import ./graft.nix { inherit pkgs lib system scions consumer; scion = self; };
          own = kit self;
          python = pkgs.python3.withPackages (ps: [ ps.pyyaml ]);
          # the seed: a workspace's source, with its notebook-kit.yaml and empty task index
          seeded = kit ./seed/common;
          names = [ "check-kb" "check-obsidian" "check-tasks" "check-templates" "just" "markdownlint-cli2"
                    "nb-convert" "nb-index" "nb-move" "upgrade-obsidian" ];
        in
        {
          inherit (own) tools apps packages;
          checks = own.checks // {
            tests = pkgs.runCommand "kit-tests" {
              nativeBuildInputs = [ python pkgs.git pkgs.just ];
              KBI_SRC = "${scions.knowledge-base-kit}/src";
              PYTHONDONTWRITEBYTECODE = "1";
            } ''
              cp -r ${self} src && chmod -R u+w src && cd src
              python -m unittest discover -s tests -v
              touch $out
            '';
            # graft.nix's contract: the tools, an app per kit tool, and the task check only for a workspace with a
            # notebook-kit.yaml (it passes on the seed)
            graft-nix =
              assert lib.assertMsg (lib.attrNames own.tools == names) "graft.nix: tools are ${toString (lib.attrNames own.tools)}";
              assert lib.assertMsg (lib.attrNames own.apps == lib.subtractLists [ "just" "markdownlint-cli2" ] names)
                "graft.nix: apps are ${toString (lib.attrNames own.apps)}";
              assert lib.assertMsg (own.checks == { }) "graft.nix: no notebook-kit.yaml, no task check";
              assert lib.assertMsg (lib.attrNames seeded.checks == [ "tasks" ]) "graft.nix: the seed gets the task check";
              pkgs.runCommand "graft-nix-test" { nativeBuildInputs = lib.attrValues own.tools; } ''
                test -e ${seeded.checks.tasks}
                test -e ${own.packages.obsidian-plugins}
                mkdir ws && cd ws
                printf 'tasks: false\n' > notebook-kit.yaml
                check-tasks --root . | grep -q 'skipped'
                touch $out
              '';
          };
        };
    };
}
