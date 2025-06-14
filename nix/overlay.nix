final: prev: {

  # This function generates a derivation based on a prompt, using an LLM over
  # the network.
  #
  # mkAIDerivation :: String -> Derivation
  #
  # Example:
  #
  # ```
  # mkAIDerivation "Generate a derivation for the latest version of xterm"
  # ```
  mkAIDerivation = final.callPackage ./mkAIDerivation {};

  ############
  ## Python ##
  ############

  # A standard Python overlay for all the Python packages necessary for ai-drv-server.
  myPythonOverlay = pfinal: pprev: {
    # A Python server for proxying calls to the OpenAI API.
    ai-drv-server = pfinal.callPackage ./pkgs/ai-drv-server {};
  };

  myPython =
    final.python312.override (oldAttrs: {
      packageOverrides =
        final.lib.composeManyExtensions
          [ (oldAttrs.packageOverrides or (_: _: {})) final.myPythonOverlay ];
    });

  # This is a Python environment with all the transitive dependencies of ai-drv-server.
  # This is used for the dev shell for working on ai-drv-server.
  #
  # myPythonWithPackages :: Derivation
  myPythonWithPackages =
    final.myPython.withPackages
      (ps:
        # TODO: How to do this properly?
        # Ideally I'd like something like haskellPackages.shellFor, but for Python.
        ps.ai-drv-server.dependencies
      );

  # A Python server for proxying calls to the OpenAI API.
  #
  # ai-drv-server :: Derivation
  ai-drv-server = final.myPython.pkgs.ai-drv-server;

  ###############
  ## dev shell ##
  ###############

  dev-shell = final.mkShell {
    nativeBuildInputs = [
      final.pyright
      final.ruff
    ];
    inputsFrom = [
      final.myPythonWithPackages.env
    ];
  };
}
