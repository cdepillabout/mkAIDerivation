final: prev: {

  mkAIDerivation = final.callPackage ./mkAIDerivation {};

  ############
  ## Python ##
  ############

  myPythonOverlay = pfinal: pprev: {
    ai-drv-server = pfinal.callPackage ./pkgs/ai-drv-server {};
  };

  myPython =
    final.python312.override (oldAttrs: {
      packageOverrides =
        final.lib.composeManyExtensions
          [ (oldAttrs.packageOverrides or (_: _: {})) final.myPythonOverlay ];
    });

  myPythonWithPackages =
    final.myPython.withPackages
      (ps:
        # TODO: How to do this properly?
        ps.ai-drv-server.dependencies
      );

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
