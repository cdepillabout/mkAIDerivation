
{ msg ? "" }:

let
  nixpkgs = import ./nix {};
in

nixpkgs.mkAIDerivation msg
