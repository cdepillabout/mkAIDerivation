# This is a default.nix for easily playing around with mkAIDerivation.
#
# You can run this from the CLI like the following:
#
# $ nix-build --argstr msg 'Generate me a derivation for that silly `sl` program that prints a steam train on the terminal.'
#
# Make sure you have the ai-drv-server running in the background.
#
# If the resulting derivation builds correctly, it should be available in `./result/`.

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
