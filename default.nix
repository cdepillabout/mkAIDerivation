
{ msg ? null }:

let
  nixpkgs = import ./nix {};

  example-prompt = ''
    Generate me a derivation for that silly `sl` program that prints a steam train on the terminal.
    Try to search the web to figure out where to download it from (hint, probably github)
  '';

  real-msg = if msg == null then example-prompt else msg;
in

nixpkgs.mkAIDerivation real-msg
