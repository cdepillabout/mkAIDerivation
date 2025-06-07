{...}:

# This file produces a full Nixpkgs, with the overlay containing
# `mkAIDerivation` applied.
#
# This is convenient to use with `nix repl`:
#
# $ nix repl ./nix
# nix-repl>
#
# Within this nix-repl, you have access to `evilDownloadUrl`:
#
# nix-repl> mkAIDerivation "Generate a derivation for the latest version of xterm";

let
  flake-lock = builtins.fromJSON (builtins.readFile ../flake.lock);

  nixpkgs-src = builtins.fetchTarball {
    url = "https://github.com/NixOS/nixpkgs/archive/${flake-lock.nodes.nixpkgs.locked.rev}.tar.gz";
    sha256 = flake-lock.nodes.nixpkgs.locked.narHash;
  };

  evil-nix-src = builtins.fetchTarball {
    url = "https://github.com/cdepillabout/evil-nixarchive/${flake-lock.nodes.evil-nix.locked.rev}.tar.gz";
    sha256 = flake-lock.nodes.evil-nix.locked.narHash;
  };

  overlays = [
    (import "${evil-nix-src}/nix/overlay.nix")
    (import ./overlay.nix)
  ];

  pkgs = import nixpkgs-src { inherit overlays; };

in

pkgs
