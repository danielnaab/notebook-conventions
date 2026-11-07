# Shared flake wiring for Markdown work-memory workspaces.
#
# In a workspace's flake.nix (see seed/common/flake.nix):
#   outputs = import "${inputs.notebook-conventions}/nix/workspace.nix" { inherit inputs; };
#
# Needs the inputs `nixpkgs` and `knowledge-base-integrity` (flake = false), and `self` (for the task check).
#
# Outputs: a dev shell; an app per kit tool (nix run .#check-kb); the task check; and packages.tools, one
# directory whose bin/ holds every kit tool plus just and markdownlint-cli2.
#
# flakeDir: where the workspace's flake.nix sits under its top, as given to graft's mkFlake (default `.`). A flake
# in a subdirectory (`nix/workspace`) keeps the workspace's content out of the Nix store, so its source holds no
# notes: there is no task check (`just check` runs check-tasks on the working tree instead).
# docs/adoption.md#a-workspace-whose-content-must-not-enter-the-nix-store
{ inputs
, systems ? [ "aarch64-darwin" "x86_64-darwin" "aarch64-linux" "x86_64-linux" ]
, withTasks ? true
, flakeDir ? "."
, extraPackages ? (_pkgs: [ ])
}:
let
  lib = inputs.nixpkgs.lib;
  kit = ../.;
  forAll = f: lib.genAttrs systems (system: f inputs.nixpkgs.legacyPackages.${system});
  python = pkgs: pkgs.python3.withPackages (ps: [ ps.pyyaml ]);
  kbiSrc = "${inputs.knowledge-base-integrity}/src";
  # the flake's source is the workspace only when the flake is at its top
  atTop = lib.elem (lib.removeSuffix "/" flakeDir) [ "." "" ];

  # name -> [ script description needsKbi ]
  tools = {
    check-kb = [ "check-kb.py" "Check links, lifecycle status, and Sources with knowledge-base-integrity" true ];
    check-templates = [ "check-templates.py" "Report how note templates differ from the pinned canonical copies" false ];
    check-obsidian = [ "check-obsidian.py"
      "Report how the vault's shared Obsidian settings and plugins differ from the kit's" false ];
    upgrade-obsidian = [ "upgrade-obsidian.py"
      "Merge the kit's seeded Obsidian settings into the vault, keeping local changes (Obsidian closed)" false ];
    index = [ "index.py" "Generate the vault's index.md listings from note frontmatter (--check: report stale ones)" true ];
    move = [ "move.py" "Move a note or folder and rewrite the links to and from it" true ];
    convert = [ "convert.py" "Convert a v0.1 workspace to the v0.2 vault layout" true ];
  } // lib.optionalAttrs withTasks {
    check-tasks = [ "check-tasks.py" "Validate current task records and their index" false ];
  };

  scripts = pkgs: lib.mapAttrs (name: spec:
    pkgs.writeShellApplication {
      inherit name;
      runtimeInputs = [ (python pkgs) ];
      text = lib.optionalString (lib.elemAt spec 2) ''
        export KBI_SRC=${kbiSrc}
      '' + ''
        exec python ${kit}/tools/${lib.elemAt spec 0} "$@"
      '';
      meta.description = lib.elemAt spec 1;
    }) tools;

  toolsPackage = pkgs: pkgs.symlinkJoin {
    name = "notebook-tools";
    paths = lib.attrValues (scripts pkgs) ++ [ pkgs.just pkgs.markdownlint-cli2 ];
    meta.description = "Every kit tool, just, and markdownlint-cli2 in one bin/";
  };
in {
  devShells = forAll (pkgs: {
    default = pkgs.mkShell {
      packages = [ pkgs.git pkgs.ripgrep (python pkgs) (toolsPackage pkgs) ] ++ extraPackages pkgs;
    };
  });

  packages = forAll (pkgs: { tools = toolsPackage pkgs; });

  apps = forAll (pkgs: lib.mapAttrs (_: drv: {
    type = "app";
    program = lib.getExe drv;
    meta.description = drv.meta.description;
  }) (scripts pkgs));

  checks = forAll (pkgs:
    lib.optionalAttrs (withTasks && atTop) {
      tasks = pkgs.runCommand "tasks-check" {
        nativeBuildInputs = [ (python pkgs) ];
        PYTHONDONTWRITEBYTECODE = "1";
      } ''
        python ${kit}/tools/check-tasks.py --root ${inputs.self}
        touch $out
      '';
    });
}
