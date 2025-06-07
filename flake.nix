{
  description = "The mkAIDerivation function, which automatically generates a derivation using OpenAI's API";

  inputs = {
    nixpkgs.url = "nixpkgs/nixpkgs-unstable";

    evil-nix.url = "github:cdepillabout/evil-nix";
    evil-nix.inputs.nixpkgs.follows = "nixpkgs";
  };

  outputs = { self, evil-nix, nixpkgs }:
    let
      supportedSystems = [ "x86_64-linux" "x86_64-darwin" "aarch64-linux" "aarch64-darwin" ];
      forAllSystems = nixpkgs.lib.genAttrs supportedSystems;
      nixpkgsFor =
        forAllSystems
          (system:
            import nixpkgs { inherit system; overlays = [ self.overlay evil-nix.overlay ]; }
          );
    in
    {
      overlay = final: prev:
        import ./nix/overlay.nix final prev //
        {
          ai-drv-example =
            final.mkAIDerivation ''
              Generate me a derivation for that silly `sl` program that
              prints a steam train on the terminal.
              You can download the source at the URL https://github.com/eyJhb/sl/archive/5.05.tar.gz
            '';
        };

      mkAIDerivation = forAllSystems (system: nixpkgsFor.${system}.mkAIDerivation);

      packages = forAllSystems (system: { inherit (nixpkgsFor.${system}) ai-drv-server ai-drv-example; });

      defaultPackage = forAllSystems (system: self.packages.${system}.ai-drv-example);

      devShell = forAllSystems (system: nixpkgsFor.${system}.dev-shell);
    };
}
