# Shared flake wiring for Markdown work-memory workspaces.
#
# In a workspace's flake.nix (see seed/common/flake.nix):
#   wiring = ./.scions/notebook-conventions/nix/workspace.nix;
#   inputs.graft.lib.mkFlake { …; outputs = import wiring { inherit inputs; }; }
#
# Needs the inputs `nixpkgs` and `knowledge-base-integrity` (flake = false), and `self`.
{ inputs
, systems ? [ "aarch64-darwin" "x86_64-darwin" "aarch64-linux" "x86_64-linux" ]
, withTasks ? true
, extraPackages ? (_pkgs: [ ])
}:
let
  lib = inputs.nixpkgs.lib;
  kit = ../.;
  forAll = f: lib.genAttrs systems (system: f inputs.nixpkgs.legacyPackages.${system});
  python = pkgs: pkgs.python3.withPackages (ps: [ ps.pyyaml ]);
  kbiSrc = "${inputs.knowledge-base-integrity}/src";
  app = pkgs: name: text: description:
    let script = pkgs.writeShellApplication {
      inherit name text;
      runtimeInputs = [ (python pkgs) ];
    };
    in { type = "app"; program = lib.getExe script; meta.description = description; };
in {
  devShells = forAll (pkgs: {
    default = pkgs.mkShell {
      packages = [ pkgs.git pkgs.ripgrep pkgs.markdownlint-cli2 (python pkgs) ] ++ extraPackages pkgs;
    };
  });

  apps = forAll (pkgs:
    {
      check-kb = app pkgs "check-kb" ''
        export KBI_SRC=${kbiSrc}
        exec python ${kit}/tools/check-kb.py "$@"
      '' "Check links, lifecycle status, and Sources with knowledge-base-integrity";
      check-templates = app pkgs "check-templates" ''
        exec python ${kit}/tools/check-templates.py "$@"
      '' "Report how note templates differ from the pinned canonical copies";
    }
    // lib.optionalAttrs withTasks {
      check-tasks = app pkgs "check-tasks" ''
        exec python ${kit}/tools/check-tasks.py "$@"
      '' "Validate current task records and their index";
    });

  checks = forAll (pkgs:
    lib.optionalAttrs withTasks {
      tasks = pkgs.runCommand "tasks-check" {
        nativeBuildInputs = [ (python pkgs) ];
        PYTHONDONTWRITEBYTECODE = "1";
      } ''
        python ${kit}/tools/check-tasks.py --root ${inputs.self}
        touch $out
      '';
    });
}
