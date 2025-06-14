{
  description = "The mkAIDerivation function, which automatically generates a derivation using OpenAI's API";

  inputs = {
    nixpkgs.url = "nixpkgs/nixpkgs-unstable";

    # This provides the evilDownloadURL function, which allows (im)pure network
    # access.
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
          # This is an example of how to use the mkAIDerivation function.
          ai-drv-example =
            final.mkAIDerivation ''
              Generate me a derivation for that silly `sl` program that
              prints a steam train on the terminal.
              You can download the source at the URL
              https://github.com/eyJhb/sl/archive/5.05.tar.gz
            '';
        };

      # Expose the mkAIDerivation at the top-level.
      #
      # As you can see in the example above, the mkAIDerivation function
      # takes a string describing the derivation you want to be generated,
      # and returns the derivation.
      #
      # mkAIDerivation :: String -> Derivation
      mkAIDerivation = forAllSystems (system: nixpkgsFor.${system}.mkAIDerivation);

      packages =
        forAllSystems
          (system:
            { inherit (nixpkgsFor.${system})
                # The server used for interfacing with the OpenAI API.
                ai-drv-server

                # The above example of using the mkAIDerivation function.
                ai-drv-example;
            }
          );

      defaultPackage = forAllSystems (system: self.packages.${system}.ai-drv-example);

      # A dev shell for working on the ai-drv-server Python server.
      devShell = forAllSystems (system: nixpkgsFor.${system}.dev-shell);

      defaultApp = forAllSystems (system: self.apps.${system}.ai-drv-server);

      apps = forAllSystems (system: {
        # This gives an easy way to run the ai-drv-server.
        ai-drv-server = {
          type = "app";
          program = "${self.packages.${system}.ai-drv-server}/bin/ai-drv-server";
        };
      });
    };
}
